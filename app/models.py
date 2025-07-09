# app/models.py

from pydantic import BaseModel, EmailStr, field_validator, model_validator
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
    submission_timestamp: Optional[datetime] = None
    
    @field_validator('submission_timestamp', mode='before')
    @classmethod
    def set_timestamp(cls, v):
        return v or datetime.now()
    
    @field_validator('consent_to_share')
    @classmethod
    def validate_consent(cls, v):
        if not v:
            raise ValueError('You must consent to share information to proceed')
        return v
    
    @model_validator(mode='after')
    def validate_conditional_fields(self):
        # Validate FAQ content
        if self.has_faqs and not self.faq_content:
            raise ValueError('FAQ content is required when FAQs are selected')
        
        # Only validate login fields if submitting through the page (not for in-person setup)
        if self.submission_method == 'Submit through this page':
            # Validate Instagram login fields (required for both plans when submitting online)
            if self.plan and not self.instagram_email:
                raise ValueError('Instagram email is required for online setup')
            if self.plan and not self.instagram_password:
                raise ValueError('Instagram password is required for online setup')
            
            # Validate Pro plan login fields
            if self.plan == 'Pro':
                if not self.tiktok_email:
                    raise ValueError('TikTok email is required for Pro plan online setup')
                if not self.tiktok_password:
                    raise ValueError('TikTok password is required for Pro plan online setup')
                if not self.facebook_email:
                    raise ValueError('Facebook email is required for Pro plan online setup')
                if not self.facebook_password:
                    raise ValueError('Facebook password is required for Pro plan online setup')
        
        return self


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    stripe_url: Optional[str] = None