# app/main.py

from dotenv import load_dotenv
load_dotenv()

import os
import json
import html
import logging
import uuid
import traceback
import re
import shutil
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import bleach
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
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

# File upload configuration
UPLOADS_DIR = BASE_DIR / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Base URL for generating absolute file URLs
BASE_URL = os.getenv('BASE_URL', 'https://aichatflows.com')
ALLOWED_EXTENSIONS = {
    'image': {'.jpg', '.jpeg', '.png', '.gif', '.webp'},
    'document': {'.pdf', '.doc', '.docx', '.txt', '.rtf'},
}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/png', 'image/gif', 'image/webp',
    'application/pdf', 'application/msword', 
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain', 'application/rtf'
}

app = FastAPI(
    title="AIChatFlows API",
    description="Secure AI-powered chatbot automation platform",
    version="1.0.0",
    docs_url=None,  # Disable docs in production
    redoc_url=None  # Disable redoc in production
)

# Rate limiting configuration with fallback
try:
    # Try to use Redis if available, otherwise fall back to in-memory
    redis_url = os.getenv("REDIS_URL") or os.getenv("RATE_LIMIT_STORAGE_URL")
    if redis_url:
        limiter = Limiter(key_func=get_remote_address, storage_uri=redis_url)
        logger.info("Rate limiting initialized with Redis backend")
    else:
        limiter = Limiter(key_func=get_remote_address)
        logger.warning("Rate limiting initialized with in-memory backend")
    
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except Exception as e:
    logger.error(f"Failed to initialize rate limiter: {e}")
    # Create a dummy limiter that doesn't actually limit to prevent crashes
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
    
    limiter = DummyLimiter()
    logger.warning("Rate limiting disabled due to initialization failure")

# Security Headers Middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        
        # Content Security Policy - Strict policy to prevent XSS
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "form-action 'self' https://buy.stripe.com; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "object-src 'none';"
        )
        
        response.headers["Content-Security-Policy"] = csp_policy
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # HSTS (HTTP Strict Transport Security) - Enable in production with HTTPS
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Remove server information
        if "server" in response.headers:
            del response.headers["server"]
        
        return response

# 2) Serve static assets from ./static
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# 3) Tell FastAPI where to find templates
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 4) Root route → landing page
@app.get("/", response_class=HTMLResponse)
@limiter.limit("30/minute")  # Rate limit: 30 requests per minute
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Start/onboarding route
@app.get("/start", response_class=HTMLResponse)
@limiter.limit("10/minute")  # Rate limit: 10 requests per minute for form access
async def start(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

# Legal page route
@app.get("/legal", response_class=HTMLResponse)
@limiter.limit("20/minute")  # Rate limit: 20 requests per minute
async def legal(request: Request):
    return templates.TemplateResponse("legal.html", {"request": request})

# Email test endpoint (for debugging)
@app.get("/test-email")
@limiter.limit("2/minute")  # Very limited for testing only
async def test_email(request: Request):
    """Test endpoint to check email configuration"""
    try:
        # Check if email service is working
        smtp_username = os.getenv('SMTP_USERNAME')
        smtp_password = os.getenv('SMTP_PASSWORD')
        admin_email = os.getenv('ADMIN_EMAIL', 'eliascolon23@gmail.com')
        
        status = {
            "email_service_type": type(email_service).__name__,
            "smtp_username_set": bool(smtp_username),
            "smtp_password_set": bool(smtp_password),
            "admin_email": admin_email,
            "smtp_server": os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            "smtp_port": os.getenv('SMTP_PORT', '587')
        }
        
        return JSONResponse(content={
            "email_configuration": status,
            "message": "Check server logs for detailed email service status"
        })
    except Exception as e:
        return JSONResponse(content={
            "error": str(e),
            "message": "Email service configuration error"
        }, status_code=500)

# Thank you page route
@app.get("/thank-you", response_class=HTMLResponse)
@limiter.limit("5/minute")  # Rate limit: 5 requests per minute for thank you page
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

# Security Middleware Configuration
# IMPORTANT: Middleware order matters - add in reverse order of execution

# Trusted Host Middleware - Only allow specific domains
render_app_name = os.getenv("RENDER_SERVICE_NAME", "aichatflows")
ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1", 
    "aichatflows.com",
    "*.aichatflows.com",
    "*.herokuapp.com",  # For Heroku deployment
    "*.onrender.com",   # For Render deployment
    "*.render.com",     # For Render deployment
    f"{render_app_name}.onrender.com"  # Specific Render app
]
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

# CORS Configuration - Secure production settings

# Environment detection with defaults
environment = os.getenv("ENVIRONMENT", "production").lower()
if environment in ["development", "dev"]:
    ALLOWED_ORIGINS = ["*"]
    logger.warning("CORS configured for development - allowing all origins")
else:
    # Production environment with Render support
    render_app_name = os.getenv("RENDER_SERVICE_NAME", "aichatflows")
    render_url = f"https://{render_app_name}.onrender.com"
    
    ALLOWED_ORIGINS = [
        "https://aichatflows.com",
        "https://www.aichatflows.com",
        render_url,  # Dynamic Render URL
        "http://localhost:8000",  # For local development
        "http://127.0.0.1:8000"   # For local development
    ]
    logger.info(f"CORS configured for production with origins: {ALLOWED_ORIGINS}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True,
    max_age=3600,  # Cache preflight requests for 1 hour
)

# Security headers middleware - add last so it runs first
app.add_middleware(SecurityHeadersMiddleware)

# Initialize email service with error handling
try:
    email_service = EmailService()
    logger.info("Email service initialized successfully")
    
    # Test if email service has credentials
    if not os.getenv('SMTP_USERNAME') or not os.getenv('SMTP_PASSWORD'):
        logger.error("Email service initialized but SMTP credentials are missing!")
        logger.error("Set SMTP_USERNAME and SMTP_PASSWORD environment variables to enable emails")
        logger.error("Without these, no emails will be sent to users or admin")
        
except Exception as e:
    logger.error(f"Failed to initialize email service: {e}")
    logger.error("Email service will be disabled - no emails will be sent")
    # Create a dummy email service that doesn't send emails to prevent crashes
    class DummyEmailService:
        def send_payment_confirmation(self, *args, **kwargs):
            logger.warning("Email service not available - skipping payment confirmation")
            return False
        
        def send_admin_payment_confirmation(self, *args, **kwargs):
            logger.warning("Email service not available - skipping admin notification")
            return False
        
        def send_user_confirmation(self, *args, **kwargs):
            logger.warning("Email service not available - skipping user confirmation")
            return False
        
        def send_admin_notification(self, *args, **kwargs):
            logger.warning("Email service not available - skipping admin notification")
            return False
        
        def send_secure_credentials(self, *args, **kwargs):
            logger.warning("Email service not available - skipping secure credentials")
            return False
    
    email_service = DummyEmailService()
    logger.warning("Email service disabled due to initialization failure")

# Startup validation
@app.on_event("startup")
async def startup_validation():
    """Validate critical dependencies on startup"""
    logger.info("Starting application startup validation...")
    
    # Validate templates directory
    templates_dir = BASE_DIR / "templates"
    if not templates_dir.exists():
        logger.error(f"Templates directory not found: {templates_dir}")
        raise RuntimeError("Templates directory missing")
    
    # Validate static files directory
    static_dir = BASE_DIR / "static"
    if not static_dir.exists():
        logger.warning(f"Static directory not found: {static_dir}")
    
    # Validate environment variables
    required_env_vars = ["ENVIRONMENT"]
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.warning(f"Missing optional environment variables: {missing_vars}")
    
    # Log startup configuration
    logger.info(f"Environment: {environment}")
    logger.info(f"Allowed hosts: {ALLOWED_HOSTS}")
    logger.info(f"CORS origins: {ALLOWED_ORIGINS}")
    logger.info(f"Rate limiter: {'Redis' if hasattr(limiter, 'storage') else 'In-memory'}")
    logger.info(f"Email service: {'Active' if hasattr(email_service, 'smtp_server') else 'Disabled'}")
    
    logger.info("Application startup validation completed successfully")

def mask_sensitive_data(data: dict) -> dict:
    """Mask sensitive credential data for logging"""
    masked_data = data.copy()
    sensitive_fields = ['instagram_password', 'tiktok_password', 'facebook_password', 'whatsapp_password']
    
    for field in sensitive_fields:
        if field in masked_data and masked_data[field]:
            masked_data[field] = "***MASKED***"
    
    return masked_data

def sanitize_input(value: Any) -> Any:
    """Comprehensive input sanitization to prevent XSS and injection attacks"""
    if value is None:
        return None
    
    if isinstance(value, str):
        # Remove null bytes and control characters
        value = value.replace('\x00', '').replace('\r', '').replace('\n', ' ')
        
        # Limit length to prevent DoS
        if len(value) > 10000:
            logger.warning(f"Input truncated - length: {len(value)}")
            value = value[:10000]
        
        # Use bleach for HTML sanitization - more robust than html.escape
        allowed_tags = []  # No HTML tags allowed
        value = bleach.clean(value, tags=allowed_tags, strip=True)
        
        # Additional sanitization for specific patterns
        value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
        value = re.sub(r'javascript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'vbscript:', '', value, flags=re.IGNORECASE)
        value = re.sub(r'onload=', '', value, flags=re.IGNORECASE)
        value = re.sub(r'onerror=', '', value, flags=re.IGNORECASE)
        
        # Strip excessive whitespace
        value = re.sub(r'\s+', ' ', value).strip()
        
        return value
    
    elif isinstance(value, (int, float, bool)):
        return value
    
    elif isinstance(value, dict):
        return {k: sanitize_input(v) for k, v in value.items()}
    
    elif isinstance(value, list):
        return [sanitize_input(item) for item in value]
    
    else:
        # Convert to string and sanitize
        return sanitize_input(str(value))

def validate_email_format(email: str) -> bool:
    """Validate email format with regex"""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def create_secure_error_response(error_type: str, message: str, request_id: str, status_code: int = 400) -> HTTPException:
    """Create secure error response that doesn't leak internal information"""
    # Log detailed error internally
    logger.error(f"[{request_id}] {error_type}: {message}")
    
    # Return generic error message to client
    safe_messages = {
        "validation": "Please check your input and try again.",
        "authentication": "Authentication failed. Please verify your credentials.",
        "authorization": "You don't have permission to access this resource.",
        "rate_limit": "Too many requests. Please try again later.",
        "server_error": "An error occurred. Please try again or contact support.",
        "not_found": "The requested resource was not found.",
        "bad_request": "Invalid request format. Please check your input."
    }
    
    safe_message = safe_messages.get(error_type, "An error occurred. Please try again.")
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error_type,
            "message": safe_message,
            "request_id": request_id,
            "timestamp": datetime.now().isoformat()
        }
    )

# File upload helper functions
def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate uploaded file for security and type compliance."""
    # Check file size
    if hasattr(file, 'size') and file.size > MAX_FILE_SIZE:
        return False, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"File type '{file.content_type}' is not allowed"
    
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    allowed_exts = set()
    for ext_group in ALLOWED_EXTENSIONS.values():
        allowed_exts.update(ext_group)
    
    if file_ext not in allowed_exts:
        return False, f"File extension '{file_ext}' is not allowed"
    
    return True, "File is valid"

def save_uploaded_file(file: UploadFile, business_name: str, file_type: str) -> str:
    """Save uploaded file and return the file URL."""
    # Create business directory
    business_dir = UPLOADS_DIR / business_name.replace(' ', '_').lower()
    business_dir.mkdir(exist_ok=True)
    
    # Generate unique filename
    file_ext = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = business_dir / unique_filename
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Return absolute URL for email compatibility
    return f"{BASE_URL}/api/files/{business_name.replace(' ', '_').lower()}/{unique_filename}"

# File upload endpoint
@app.post("/api/upload-file")
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    business_name: str = Form(...),
    file_type: str = Form(...)
):
    """Upload a file and return its URL."""
    request_id = str(uuid.uuid4())[:8]
    logger.info(f"[{request_id}] File upload request: {file.filename} for {business_name}")
    
    try:
        # Validate file
        is_valid, message = validate_file(file)
        if not is_valid:
            logger.warning(f"[{request_id}] File validation failed: {message}")
            raise HTTPException(status_code=400, detail=message)
        
        # Save file
        file_url = save_uploaded_file(file, business_name, file_type)
        
        logger.info(f"[{request_id}] File uploaded successfully: {file_url}")
        return {
            "success": True,
            "file_url": file_url,
            "filename": file.filename,
            "file_type": file.content_type,
            "size": file.size if hasattr(file, 'size') else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] File upload error: {str(e)}")
        raise HTTPException(status_code=500, detail="File upload failed")

# File serving endpoint
@app.get("/api/files/{business_name}/{filename}")
async def serve_file(business_name: str, filename: str):
    """Serve uploaded files with proper security."""
    try:
        file_path = UPLOADS_DIR / business_name / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Verify file is within uploads directory (security check)
        if not str(file_path.resolve()).startswith(str(UPLOADS_DIR.resolve())):
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # Create response with proper headers for email client compatibility
        response = FileResponse(
            path=str(file_path),
            media_type=mime_type,
            filename=filename
        )
        
        # Add headers for better email client compatibility
        response.headers["Cache-Control"] = "public, max-age=3600"
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET"
        response.headers["Content-Disposition"] = f'inline; filename="{filename}"'
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"File serving error: {str(e)}")
        raise HTTPException(status_code=500, detail="File access failed")

# Onboarding form submission endpoint
@app.post("/api/submit-onboarding", response_model=OnboardingResponse)
@limiter.limit("3/minute")  # Rate limit: 3 form submissions per minute per IP
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
            raise create_secure_error_response("bad_request", "Invalid request format", request_id, 400)
        
        # Enhanced data processing and cleaning with security
        def process_form_data(data):
            """Clean and process form data before validation with comprehensive sanitization"""
            processed = {}
            
            # Handle all fields with sanitization
            for key, value in data.items():
                # Convert empty strings and null values to None for optional fields
                if value in ["", "null", "undefined", None]:
                    processed[key] = None
                # Handle boolean fields
                elif key in ['has_faqs', 'consent_to_share', 'confirm_accurate', 'consent_automation']:
                    if isinstance(value, str):
                        processed[key] = value.lower() == 'true'
                    elif isinstance(value, bool):
                        processed[key] = value
                    else:
                        processed[key] = bool(value) if value is not None else False
                else:
                    # Apply comprehensive sanitization to all other fields
                    processed[key] = sanitize_input(value)
            
            return processed
        
        # Process form data with sanitization
        processed_data = process_form_data(request_data)
        
        # Additional validation for critical fields
        if processed_data.get('contact_email'):
            if not validate_email_format(processed_data['contact_email']):
                raise create_secure_error_response("validation", "Invalid email format", request_id, 422)
        
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
            
            # Create user-friendly error messages without exposing internal structure
            error_messages = []
            for error in e.errors():
                field_name = error['loc'][-1] if error['loc'] else 'field'
                error_type = error['type']
                
                # Sanitize field names and provide generic error messages
                safe_field_name = sanitize_input(str(field_name)).replace('_', ' ').title()
                
                # Custom error messages for better UX but no internal details
                if error_type == 'missing':
                    error_messages.append(f"{safe_field_name} is required")
                elif 'email' in error_type.lower():
                    error_messages.append(f"{safe_field_name} must be a valid email address")
                else:
                    error_messages.append(f"{safe_field_name} is invalid")
            
            raise create_secure_error_response("validation", f"Validation failed: {'; '.join(error_messages)}", request_id, 422)
        
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
            sensitive_fields = ['instagram_password', 'facebook_password', 'other_platform_credentials']
            storage_data = {k: v for k, v in sanitized_data.items() if k not in sensitive_fields}
            storage_data['credentials_handling'] = 'Sent via secure email'
        else:
            logger.info(f"[{request_id}] Processing in-person setup request")
            
            # For in-person setup, don't store any login credentials
            non_credential_fields = [
                'business_name', 'instagram_handle', 'other_platforms', 'business_type',
                'common_customer_question', 'product_service_description', 'delivery_pickup',
                'delivery_services', 'delivery_other', 'pickup_method', 'pickup_details',
                'menu_upload', 'menu_text', 'additional_docs', 'plan', 'submission_method',
                'has_faqs', 'faq_upload', 'consent_to_share', 'confirm_accurate', 'consent_automation',
                'contact_email', 'submission_timestamp'
            ]
            storage_data = {k: v for k, v in sanitized_data.items() if k in non_credential_fields}
            storage_data['credentials_handling'] = 'In-person setup requested'
        
        storage_data['request_id'] = request_id
        logger.info(f"[{request_id}] Storage data prepared")
        
        # Save sanitized, non-sensitive data to file with enhanced error handling
        try:
            submissions_dir = BASE_DIR / "submissions"
            
            # Create directory with proper error handling
            try:
                submissions_dir.mkdir(exist_ok=True, parents=True)
            except PermissionError:
                logger.warning(f"[{request_id}] No write permission for submissions directory, using temp directory")
                submissions_dir = Path("/tmp") / "submissions"
                submissions_dir.mkdir(exist_ok=True, parents=True)
            except Exception as dir_error:
                logger.error(f"[{request_id}] Failed to create submissions directory: {dir_error}")
                # Use current directory as final fallback
                submissions_dir = Path(".")
            
            timestamp = storage_data['submission_timestamp'].isoformat()
            safe_business_name = "".join(c for c in storage_data['business_name'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"submission_{safe_business_name.replace(' ', '_')}_{timestamp}.json"
            filepath = submissions_dir / filename
            
            with open(filepath, 'w') as f:
                json.dump(storage_data, f, indent=2, default=str)
            logger.info(f"[{request_id}] Submission saved to {filepath}")
            
        except Exception as e:
            logger.error(f"[{request_id}] Failed to save submission: {str(e)}")
            logger.error(f"[{request_id}] File save traceback: {traceback.format_exc()}")
            # Continue processing even if file save fails - email notifications still work
        
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
        
        # Generate secure payment URL - URLs now stored server-side only
        # TODO: SECURITY - Move Stripe URLs to environment variables
        stripe_urls = {
            "Starter": os.getenv("STRIPE_STARTER_URL", "https://buy.stripe.com/fZu5kEaZ4dQqbKUfNZ8Vi00"),
            "Pro": os.getenv("STRIPE_PRO_URL", "https://buy.stripe.com/3cI5kE7MS13EcOY6dp8Vi01")
        }
        
        stripe_url = stripe_urls.get(form_data.plan)
        
        # Add success URL parameter securely
        success_url = os.getenv("SUCCESS_URL", "https://aichatflows.com/thank-you")
        if "?" in stripe_url:
            stripe_url += f"&success_url={success_url}"
        else:
            stripe_url += f"?success_url={success_url}"
            
        logger.info(f"[{request_id}] Payment URL generated for {form_data.plan} plan")
        
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
        
        raise create_secure_error_response("server_error", "Unexpected error during form submission", request_id, 500)