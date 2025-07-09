# app/models.py

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, Literal, List
from datetime import datetime


class OnboardingForm(BaseModel):
    # Business Info
    business_name: str
    instagram_handle: str
    other_platforms: Optional[str] = None
    business_type: str
    common_customer_question: str
    
    # Service Details
    delivery_pickup: Literal["Delivery", "Pickup", "Both", "None"]
    product_service_description: str
    has_faqs: bool
    faq_content: Optional[str] = None
    
    # Plan Selection
    plan: Literal["Starter", "Pro"]
    
    # Social Media Logins (conditional based on plan)
    instagram_email: Optional[EmailStr] = None
    instagram_password: Optional[str] = None
    
    # Pro plan additional logins
    tiktok_email: Optional[EmailStr] = None
    tiktok_password: Optional[str] = None
    facebook_email: Optional[EmailStr] = None
    facebook_password: Optional[str] = None
    whatsapp_number: Optional[str] = None
    whatsapp_password: Optional[str] = None
    
    # Secure submission method
    submission_method: Literal["Submit through this page", "Request In-Person Setup"]
    
    # Legal
    consent_to_share: bool
    
    # Contact
    contact_email: EmailStr
    
    # Auto-generated
    submission_timestamp: datetime = None
    
    @validator('submission_timestamp', pre=True, always=True)
    def set_timestamp(cls, v):
        return v or datetime.now()
    
    @validator('faq_content')
    def validate_faq_content(cls, v, values):
        if values.get('has_faqs') and not v:
            raise ValueError('FAQ content is required when has_faqs is True')
        return v
    
    @validator('instagram_email', 'instagram_password')
    def validate_instagram_login(cls, v, values, field):
        if values.get('plan') and not v:
            raise ValueError(f'{field.name.replace("_", " ").title()} is required for both plans')
        return v
    
    @validator('tiktok_email', 'tiktok_password', 'facebook_email', 
               'facebook_password', 'whatsapp_number', 'whatsapp_password')
    def validate_pro_logins(cls, v, values, field):
        if values.get('plan') == 'Pro' and values.get('submission_method') == 'Submit through this page':
            platform = field.name.split('_')[0]
            if platform in ['tiktok', 'facebook'] and not v:
                raise ValueError(f'{field.name.replace("_", " ").title()} is required for Pro plan')
        return v
    
    @validator('consent_to_share')
    def validate_consent(cls, v):
        if not v:
            raise ValueError('You must consent to share information to proceed')
        return v


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    stripe_url: Optional[str] = None