# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
import json
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
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
        # Convert form data to dict
        data_dict = form_data.dict()
        
        # Save submission to file (since no database)
        submissions_dir = BASE_DIR / "submissions"
        submissions_dir.mkdir(exist_ok=True)
        
        timestamp = data_dict['submission_timestamp'].isoformat()
        filename = f"submission_{data_dict['business_name'].replace(' ', '_')}_{timestamp}.json"
        filepath = submissions_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(data_dict, f, indent=2, default=str)
        
        # Send confirmation email to user
        email_service.send_user_confirmation(form_data.contact_email, data_dict)
        
        # Send notification email to admin
        email_service.send_admin_notification(data_dict)
        
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
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


