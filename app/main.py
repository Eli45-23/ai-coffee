# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
import json
import html
import logging
import uuid
import traceback
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from .models import OnboardingForm, OnboardingResponse
from .email_service import EmailService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Thank you page route
@app.get("/thank-you", response_class=HTMLResponse)
async def thank_you(request: Request):
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    logger.info(f"[{request_id}] Thank you page accessed from IP: {request.client.host if request.client else 'unknown'}")
    
    # Initialize variables for safe access
    submission_data = None
    business_name = "Valued Customer"
    plan = "Unknown"
    user_email = None
    
    try:
        # Safely get the most recent submission from the submissions directory
        submissions_dir = BASE_DIR / "submissions"
        
        # Check if submissions directory exists and is accessible
        try:
            if not submissions_dir.exists():
                logger.warning(f"[{request_id}] Submissions directory does not exist at {submissions_dir}")
                raise FileNotFoundError("Submissions directory not found")
            
            if not submissions_dir.is_dir():
                logger.error(f"[{request_id}] Submissions path exists but is not a directory")
                raise OSError("Submissions path is not a directory")
                
        except (OSError, PermissionError) as e:
            logger.error(f"[{request_id}] Cannot access submissions directory: {str(e)}")
            logger.error(f"[{request_id}] Directory access traceback: {traceback.format_exc()}")
            # Continue to render page without email functionality
            return templates.TemplateResponse("thank-you.html", {"request": request})
        
        # Safely find and load the most recent submission file
        try:
            # Get all submission files with error handling
            submission_files = []
            try:
                submission_files = list(submissions_dir.glob("submission_*.json"))
            except (OSError, PermissionError) as e:
                logger.error(f"[{request_id}] Error listing submission files: {str(e)}")
                raise
            
            if not submission_files:
                logger.warning(f"[{request_id}] No submission files found in {submissions_dir}")
                # Render page without triggering emails
                return templates.TemplateResponse("thank-you.html", {"request": request})
            
            logger.info(f"[{request_id}] Found {len(submission_files)} submission files")
            
            # Safely get the most recent file by modification time with validation
            try:
                latest_file = max(submission_files, key=lambda f: f.stat().st_mtime)
                
                # Validate the selected file
                if not latest_file.exists():
                    logger.error(f"[{request_id}] Latest file {latest_file} no longer exists")
                    raise FileNotFoundError("Latest submission file missing")
                    
                if not latest_file.is_file():
                    logger.error(f"[{request_id}] Latest path {latest_file} is not a file")
                    raise OSError("Latest submission path is not a file")
                    
                # Check file size (prevent loading huge files)
                file_size = latest_file.stat().st_size
                if file_size > 1024 * 1024:  # 1MB limit
                    logger.error(f"[{request_id}] Submission file too large: {file_size} bytes")
                    raise ValueError("Submission file too large")
                    
                if file_size == 0:
                    logger.warning(f"[{request_id}] Submission file is empty")
                    raise ValueError("Submission file is empty")
                    
                logger.info(f"[{request_id}] Selected latest submission: {latest_file.name} ({file_size} bytes)")
                
            except (OSError, ValueError, PermissionError) as e:
                logger.error(f"[{request_id}] Error selecting latest file: {str(e)}")
                logger.error(f"[{request_id}] File selection traceback: {traceback.format_exc()}")
                return templates.TemplateResponse("thank-you.html", {"request": request})
            
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error during file discovery: {str(e)}")
            logger.error(f"[{request_id}] File discovery traceback: {traceback.format_exc()}")
            return templates.TemplateResponse("thank-you.html", {"request": request})
        
        # Safely read and parse the submission data
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                submission_data = json.load(f)
            
            # Validate JSON structure
            if not isinstance(submission_data, dict):
                logger.error(f"[{request_id}] Invalid JSON structure: not a dictionary")
                raise ValueError("Invalid submission data structure")
            
            # Safely extract data with validation and sanitization
            business_name = str(submission_data.get('business_name', 'Valued Customer')).strip()
            plan = str(submission_data.get('plan', 'Unknown')).strip()
            user_email = submission_data.get('contact_email')
            
            # Validate business name (prevent XSS and ensure reasonable length)
            if len(business_name) > 200:
                logger.warning(f"[{request_id}] Business name too long, truncating")
                business_name = business_name[:200] + "..."
            
            # Validate email format if present
            if user_email:
                user_email = str(user_email).strip()
                if '@' not in user_email or len(user_email) > 254:
                    logger.warning(f"[{request_id}] Invalid email format detected")
                    user_email = None
            
            # Mask sensitive data for logging
            masked_data = mask_sensitive_data(submission_data)
            logger.info(f"[{request_id}] Loaded submission data for {business_name} ({plan} Plan)")
            logger.debug(f"[{request_id}] Submission data keys: {list(masked_data.keys())}")
            
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            logger.error(f"[{request_id}] Failed to parse submission file {latest_file}: {str(e)}")
            logger.error(f"[{request_id}] JSON parsing traceback: {traceback.format_exc()}")
            return templates.TemplateResponse("thank-you.html", {"request": request})
            
        except (OSError, PermissionError) as e:
            logger.error(f"[{request_id}] Failed to read submission file {latest_file}: {str(e)}")
            logger.error(f"[{request_id}] File read traceback: {traceback.format_exc()}")
            return templates.TemplateResponse("thank-you.html", {"request": request})
            
        except Exception as e:
            logger.error(f"[{request_id}] Unexpected error reading submission data: {str(e)}")
            logger.error(f"[{request_id}] Data reading traceback: {traceback.format_exc()}")
            return templates.TemplateResponse("thank-you.html", {"request": request})
        
        # Send confirmation emails with comprehensive error handling
        if user_email and submission_data:
            # Send payment confirmation email to user
            try:
                logger.info(f"[{request_id}] Attempting to send payment confirmation to user")
                email_result = email_service.send_payment_confirmation(user_email, business_name, plan)
                
                if email_result:
                    logger.info(f"[{request_id}] Payment confirmation email sent successfully to {user_email}")
                else:
                    logger.warning(f"[{request_id}] Payment confirmation email failed - service returned False")
                    
            except Exception as e:
                logger.error(f"[{request_id}] Failed to send payment confirmation email: {str(e)}")
                logger.error(f"[{request_id}] User email traceback: {traceback.format_exc()}")
                # Continue processing - don't fail the entire request
            
            # Send admin notification about completed payment
            try:
                logger.info(f"[{request_id}] Attempting to send admin payment notification")
                admin_result = email_service.send_admin_payment_confirmation(business_name, plan, user_email)
                
                if admin_result:
                    logger.info(f"[{request_id}] Admin payment confirmation email sent successfully")
                else:
                    logger.warning(f"[{request_id}] Admin payment confirmation email failed - service returned False")
                    
            except Exception as e:
                logger.error(f"[{request_id}] Failed to send admin payment confirmation: {str(e)}")
                logger.error(f"[{request_id}] Admin email traceback: {traceback.format_exc()}")
                # Continue processing - don't fail the entire request
        else:
            if not user_email:
                logger.warning(f"[{request_id}] No valid user email found - skipping email notifications")
            if not submission_data:
                logger.warning(f"[{request_id}] No submission data available - skipping email notifications")
                
    except Exception as e:
        logger.error(f"[{request_id}] Unexpected error processing thank you page: {str(e)}")
        logger.error(f"[{request_id}] Full processing traceback: {traceback.format_exc()}")
        # Continue to render page - never fail completely
    
    # Calculate processing time for monitoring
    processing_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"[{request_id}] Thank you page processing completed in {processing_time:.3f}s")
    
    # Always render the thank you page with graceful fallback
    try:
        return templates.TemplateResponse("thank-you.html", {"request": request})
    except Exception as e:
        logger.error(f"[{request_id}] Failed to render thank-you template: {str(e)}")
        logger.error(f"[{request_id}] Template rendering traceback: {traceback.format_exc()}")
        
        # Last resort fallback - return minimal HTML
        minimal_html = """
        <!DOCTYPE html>
        <html><head><title>Thank You - AIChatFlows</title></head>
        <body>
        <h1>Thank You!</h1>
        <p>Your payment has been confirmed. We'll be in touch soon.</p>
        <a href="/">Return Home</a>
        </body></html>
        """
        return HTMLResponse(content=minimal_html, status_code=200)

# 5) CORS (allow your front-end fetch)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # in prod, lock this to your domain
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Initialize email service
email_service = EmailService()

def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive credential data for logging"""
    masked_data = data.copy()
    sensitive_fields = ['instagram_password', 'tiktok_password', 'facebook_password', 'whatsapp_password']
    
    for field in sensitive_fields:
        if field in masked_data and masked_data[field]:
            masked_data[field] = "***MASKED***"
    
    return masked_data

# Onboarding form submission endpoint
@app.post("/api/submit-onboarding", response_model=OnboardingResponse)
async def submit_onboarding(request: Request):
    # Generate unique request ID for tracking
    request_id = str(uuid.uuid4())[:8]
    start_time = datetime.now()
    
    logger.info(f"[{request_id}] Starting onboarding form submission")
    
    try:
        # Parse request body
        try:
            raw_body = await request.body()
            logger.info(f"[{request_id}] Raw request body length: {len(raw_body)} bytes")
            
            request_data = await request.json()
            logger.info(f"[{request_id}] Parsed JSON keys: {list(request_data.keys())}")
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to parse request body: {str(e)}")
            logger.error(f"[{request_id}] Full traceback: {traceback.format_exc()}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid request format",
                    "message": "Request body must be valid JSON",
                    "request_id": request_id
                }
            )
        
        # Enhanced data processing and cleaning
        def process_form_data(data):
            """Clean and process form data before validation"""
            processed = {}
            
            # Handle all fields
            for key, value in data.items():
                # Convert empty strings and null values to None for optional fields
                if value in ["", "null", "undefined", None]:
                    processed[key] = None
                # Handle boolean fields
                elif key in ['has_faqs', 'consent_to_share']:
                    if isinstance(value, str):
                        processed[key] = value.lower() == 'true'
                    elif isinstance(value, bool):
                        processed[key] = value
                    else:
                        processed[key] = bool(value) if value is not None else False
                else:
                    processed[key] = value
            
            return processed
        
        # Process form data
        processed_data = process_form_data(request_data)
        
        # Log submission details (with masked sensitive data)
        masked_data = mask_sensitive_data(processed_data)
        logger.info(f"[{request_id}] Processed data: {masked_data}")
        logger.info(f"[{request_id}] Submission method: {processed_data.get('submission_method', 'MISSING')}")
        logger.info(f"[{request_id}] Plan: {processed_data.get('plan', 'MISSING')}")
        
        # Enhanced login field clearing for in-person setup
        if processed_data.get('submission_method') == 'Request In-Person Setup':
            logger.info(f"[{request_id}] In-person setup detected, clearing all login fields")
            login_fields = [
                'instagram_email', 'instagram_password', 'tiktok_email', 'tiktok_password',
                'facebook_email', 'facebook_password', 'whatsapp_number', 'whatsapp_password'
            ]
            for field in login_fields:
                processed_data[field] = None
            logger.info(f"[{request_id}] Login fields cleared for in-person setup")
        
        # Validate with Pydantic with enhanced error handling
        try:
            form_data = OnboardingForm(**processed_data)
            logger.info(f"[{request_id}] Pydantic validation successful")
            
        except ValidationError as e:
            logger.error(f"[{request_id}] Pydantic validation failed")
            logger.error(f"[{request_id}] Validation errors: {e.errors()}")
            logger.error(f"[{request_id}] Full traceback: {traceback.format_exc()}")
            
            # Create user-friendly error messages
            error_messages = []
            for error in e.errors():
                field_name = error['loc'][-1] if error['loc'] else 'field'
                error_msg = error['msg']
                error_type = error['type']
                
                # Custom error messages for better UX
                if error_type == 'missing':
                    error_messages.append(f"{field_name.replace('_', ' ').title()} is required")
                elif error_type == 'value_error':
                    if 'required' in error_msg.lower():
                        error_messages.append(f"{field_name.replace('_', ' ').title()} is required")
                    else:
                        error_messages.append(f"{field_name.replace('_', ' ').title()}: {error_msg}")
                elif 'email' in error_type.lower():
                    error_messages.append(f"{field_name.replace('_', ' ').title()} must be a valid email address")
                else:
                    error_messages.append(f"{field_name.replace('_', ' ').title()}: {error_msg}")
            
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "Validation failed",
                    "messages": error_messages,
                    "request_id": request_id
                }
            )
        
        # Convert form data to dict and sanitize inputs
        data_dict = form_data.dict()
        logger.info(f"[{request_id}] Form data converted to dict successfully")
        
        # Sanitize string inputs to prevent XSS
        sanitized_data = {}
        for key, value in data_dict.items():
            if isinstance(value, str):
                sanitized_data[key] = html.escape(value)
            else:
                sanitized_data[key] = value
        
        logger.info(f"[{request_id}] Data sanitization completed")
        
        # Handle secure credential storage based on submission method
        if form_data.submission_method == 'Submit through this page':
            logger.info(f"[{request_id}] Processing online submission with credentials")
            
            # Send credentials via secure email immediately, then remove from storage
            try:
                email_service.send_secure_credentials(form_data.contact_email, sanitized_data)
                logger.info(f"[{request_id}] Secure credentials email sent successfully")
            except Exception as e:
                logger.error(f"[{request_id}] Failed to send secure credentials email: {str(e)}")
                logger.error(f"[{request_id}] Email error traceback: {traceback.format_exc()}")
                # Continue processing even if email fails
            
            # Remove sensitive fields from data that gets stored
            sensitive_fields = ['instagram_password', 'tiktok_password', 'facebook_password', 'whatsapp_password']
            storage_data = {k: v for k, v in sanitized_data.items() if k not in sensitive_fields}
            storage_data['credentials_handling'] = 'Sent via secure email'
        else:
            logger.info(f"[{request_id}] Processing in-person setup request")
            
            # For in-person setup, don't store any login credentials
            non_credential_fields = [
                'business_name', 'instagram_handle', 'other_platforms', 'business_type',
                'common_customer_question', 'delivery_pickup', 'product_service_description',
                'has_faqs', 'faq_content', 'plan', 'submission_method', 'consent_to_share',
                'contact_email', 'submission_timestamp'
            ]
            storage_data = {k: v for k, v in sanitized_data.items() if k in non_credential_fields}
            storage_data['credentials_handling'] = 'In-person setup requested'
        
        storage_data['request_id'] = request_id
        logger.info(f"[{request_id}] Storage data prepared")
        
        # Save sanitized, non-sensitive data to file with enhanced error handling
        try:
            submissions_dir = BASE_DIR / "submissions"
            submissions_dir.mkdir(exist_ok=True)
            
            timestamp = storage_data['submission_timestamp'].isoformat()
            safe_business_name = "".join(c for c in storage_data['business_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"submission_{safe_business_name.replace(' ', '_')}_{timestamp}.json"
            filepath = submissions_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            logger.info(f"[{request_id}] Submission saved to {filepath}")
            
        except OSError as e:
            logger.error(f"[{request_id}] Failed to create submissions directory: {e}")
            logger.error(f"[{request_id}] File error traceback: {traceback.format_exc()}")
            # Try fallback directory
            try:
                fallback_path = Path(".") / f"submission_{request_id}.json"
                with open(fallback_path, 'w') as f:
                    json.dump(storage_data, f, indent=2, default=str)
                logger.info(f"[{request_id}] Submission saved to fallback location: {fallback_path}")
            except Exception as fallback_error:
                logger.error(f"[{request_id}] Failed to save submission even to fallback: {fallback_error}")
                
        except Exception as e:
            logger.error(f"[{request_id}] Failed to save submission: {str(e)}")
            logger.error(f"[{request_id}] File save traceback: {traceback.format_exc()}")
        
        # Send confirmation email to user with enhanced error handling
        try:
            email_service.send_user_confirmation(form_data.contact_email, storage_data)
            logger.info(f"[{request_id}] User confirmation email sent successfully")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to send user confirmation email: {str(e)}")
            logger.error(f"[{request_id}] User email traceback: {traceback.format_exc()}")
        
        # Send notification email to admin with enhanced error handling
        try:
            email_service.send_admin_notification(storage_data)
            logger.info(f"[{request_id}] Admin notification email sent successfully")
        except Exception as e:
            logger.error(f"[{request_id}] Failed to send admin notification email: {str(e)}")
            logger.error(f"[{request_id}] Admin email traceback: {traceback.format_exc()}")
        
        # Determine Stripe URL based on plan with success_url redirect
        stripe_urls = {
            "Starter": "https://buy.stripe.com/fZu5kEaZ4dQqbKUfNZ8Vi00?success_url=https://aichatflows.com/thank-you",
            "Pro": "https://buy.stripe.com/3cI5kE7MS13EcOY6dp8Vi01?success_url=https://aichatflows.com/thank-you"
        }
        
        stripe_url = stripe_urls.get(form_data.plan)
        logger.info(f"[{request_id}] Stripe URL selected: {stripe_url}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"[{request_id}] Form submission completed successfully in {processing_time:.2f}s")
        
        return OnboardingResponse(
            success=True,
            message="Thank you for joining AIChatFlows! Redirecting to payment...",
            stripe_url=stripe_url
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without modification
        raise
        
    except Exception as e:
        # Handle all other unexpected errors with full traceback logging
        logger.error(f"[{request_id}] Unexpected error during form submission: {str(e)}")
        logger.error(f"[{request_id}] Full traceback: {traceback.format_exc()}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again or contact support.",
                "request_id": request_id
            }
        )