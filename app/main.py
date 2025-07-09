# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
import json
import html
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from .models import OnboardingForm, OnboardingResponse
from .email_service import EmailService

# Get the parent directory (ai-coffee root)
BASE_DIR = Path(__file__).parent.parent

app = FastAPI()

# 2) Serve static assets from ./static
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 3) Tell FastAPI where to find templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 4) Root route → landing page
@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Start/onboarding route
@app.get("/start", response_class=HTMLResponse)
async def start(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

# Legal page route
@app.get("/legal", response_class=HTMLResponse)
async def legal(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

# 5) CORS (allow your front-end fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # in prod, lock this to your domain
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize email service
email_service = EmailService()

# Onboarding form submission endpoint
@app.post("/api/submit-onboarding", response_model=OnboardingResponse)
async def submit_onboarding(form_data: OnboardingForm):
    try:
        # Convert form data to dict and sanitize inputs
        data_dict = form_data.dict()
        
        # Sanitize string inputs to prevent XSS
        sanitized_data = {}
        for key, value in data_dict.items():
            if isinstance(value, str):
                sanitized_data[key] = html.escape(value)
            else:
                sanitized_data[key] = value
        
        # Handle secure credential storage based on submission method
        if form_data.submission_method == 'Submit through this page':
            # Send credentials via secure email immediately, then remove from storage
            email_service.send_secure_credentials(form_data.contact_email, sanitized_data)
            
            # Remove sensitive fields from data that gets stored
            sensitive_fields = ['instagram_password', 'tiktok_password', 'facebook_password', 'whatsapp_password']
            storage_data = {k: v for k, v in sanitized_data.items() if k not in sensitive_fields}
            storage_data['credentials_handling'] = 'Sent via secure email'
        else:
            # For in-person setup, don't store any login credentials
            non_credential_fields = [
                'business_name', 'instagram_handle', 'other_platforms', 'business_type',
                'common_customer_question', 'delivery_pickup', 'product_service_description',
                'has_faqs', 'faq_content', 'plan', 'submission_method', 'consent_to_share',
                'contact_email', 'submission_timestamp'
            ]
            storage_data = {k: v for k, v in sanitized_data.items() if k in non_credential_fields}
            storage_data['credentials_handling'] = 'In-person setup requested'
        
        # Save sanitized, non-sensitive data to file
        try:
            submissions_dir = BASE_DIR / "submissions"
            submissions_dir.mkdir(exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create submissions directory: {e}")
            # Fallback to current directory if submissions dir can't be created
            submissions_dir = Path(".")
        
        timestamp = storage_data['submission_timestamp'].isoformat()
        safe_business_name = "".join(c for c in storage_data['business_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"submission_{safe_business_name.replace(' ', '_')}_{timestamp}.json"
        filepath = submissions_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(storage_data, f, indent=2, default=str)
        
        # Send confirmation email to user
        email_service.send_user_confirmation(form_data.contact_email, storage_data)
        
        # Send notification email to admin (without sensitive credentials)
        email_service.send_admin_notification(storage_data)
        
        # Determine Stripe URL based on plan
        stripe_urls = {
            "Starter": "https://buy.stripe.com/fZu5kEaZ4dQqbKUfNZ8Vi00",
            "Pro": "https://buy.stripe.com/3cI5kE7MS13EcOY6dp8Vi01"
        }
        
        stripe_url = stripe_urls.get(form_data.plan)
        
        return OnboardingResponse(
            success=True,
            message="Thank you for joining AIChatFlows! Redirecting to payment...",
            stripe_url=stripe_url
        )
        
    except ValidationError as e:
        # Handle Pydantic validation errors with user-friendly messages
        error_messages = []
        for error in e.errors():
            field_name = error['loc'][-1] if error['loc'] else 'field'
            error_msg = error['msg']
            error_messages.append(f"{field_name.replace('_', ' ').title()}: {error_msg}")
        
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Validation failed",
                "messages": error_messages
            }
        )
    except Exception as e:
        # Handle other errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again."
            }
        )


