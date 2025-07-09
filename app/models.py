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
    product_service_description: str
    
    # Delivery & Pickup Info
    delivery_pickup: Literal["Delivery", "Pickup", "Both", "Neither"]
    delivery_services: Optional[str] = None  # Comma-separated list
    delivery_other: Optional[str] = None
    pickup_method: Optional[str] = None
    pickup_details: Optional[str] = None
    
    # Menu Submission
    menu_upload: Optional[str] = None  # File path or base64
    menu_text: Optional[str] = None
    additional_docs: Optional[str] = None  # Multiple file paths
    
    # Plan Selection
    plan: Literal["Starter", "Pro"]
    
    # Social Media Logins (conditional based on plan)
    instagram_email: Optional[str] = None  # Changed to str for username
    instagram_password: Optional[str] = None
    
    # Pro plan additional logins
    facebook_email: Optional[str] = None  # Changed to str for username
    facebook_password: Optional[str] = None
    other_platform_credentials: Optional[str] = None
    
    # Secure submission method
    submission_method: Literal["Submit through this page", "Use SendSecure.ly", "Request In-Person Setup"]
    
    # FAQ Support
    has_faqs: bool
    faq_upload: Optional[str] = None  # File path
    
    # Legal & Consent
    consent_to_share: bool
    confirm_accurate: bool
    consent_automation: bool
    
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
    
    # Convert empty strings to None for optional fields
    @field_validator('instagram_email', 'instagram_password', 'facebook_email', 'facebook_password', 
                     'other_platforms', 'other_platform_credentials', 'delivery_services', 'delivery_other',
                     'pickup_method', 'pickup_details', 'menu_upload', 'menu_text', 'additional_docs', 
                     'faq_upload', mode='before')
    @classmethod
    def convert_empty_strings_to_none(cls, v):
        if v == "" or v == "null" or v == "undefined":
            return None
        return v
    
    @model_validator(mode='after')
    def validate_conditional_fields(self):
        # Validate FAQ upload when has_faqs is true
        if self.has_faqs and not self.faq_upload:
            raise ValueError('FAQ document upload is required when FAQs are selected')
        
        # Validate menu submission (either upload or text required)
        if not self.menu_upload and not self.menu_text:
            raise ValueError('Either menu upload or menu text is required')
        
        # Validate delivery services when delivery is selected
        if self.delivery_pickup in ['Delivery', 'Both']:
            if not self.delivery_services and not self.delivery_other:
                raise ValueError('Delivery service selection is required when delivery is offered')
        
        # Validate pickup method when pickup is selected
        if self.delivery_pickup in ['Pickup', 'Both']:
            if not self.pickup_method:
                raise ValueError('Pickup method is required when pickup is offered')
        
        # Only validate login fields if submitting through the page (not for other methods)
        if self.submission_method == 'Submit through this page':
            # Validate Instagram login fields (required for both plans when submitting online)
            if not self.instagram_email:
                raise ValueError('Instagram username is required for online setup')
            if not self.instagram_password:
                raise ValueError('Instagram password is required for online setup')
            
            # Validate Pro plan login fields (Facebook is optional but if provided, both fields needed)
            if self.plan == 'Pro':
                if self.facebook_email and not self.facebook_password:
                    raise ValueError('Facebook password is required when Facebook username is provided')
                if self.facebook_password and not self.facebook_email:
                    raise ValueError('Facebook username is required when Facebook password is provided')
        
        return self


class OnboardingResponse(BaseModel):
    success: bool
    message: str
    stripe_url: Optional[str] = None