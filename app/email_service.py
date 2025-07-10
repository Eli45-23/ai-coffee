# app/email_service.py

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any
import json
from datetime import datetime


class EmailService:
    def __init__(self):
        import logging
        logger = logging.getLogger(__name__)
        
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.admin_email = os.getenv('ADMIN_EMAIL', 'eliascolon23@gmail.com')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@aichatflows.com')
        
        # Log configuration status
        logger.info(f"Email Service Configuration:")
        logger.info(f"  SMTP Server: {self.smtp_server}:{self.smtp_port}")
        logger.info(f"  From Email: {self.from_email}")
        logger.info(f"  Admin Email: {self.admin_email}")
        logger.info(f"  SMTP Username: {'✓ Set' if self.smtp_username else '✗ Missing'}")
        logger.info(f"  SMTP Password: {'✓ Set' if self.smtp_password else '✗ Missing'}")
        
        if not self.smtp_username or not self.smtp_password:
            logger.error("CRITICAL: Email service cannot send emails - SMTP credentials missing!")
            logger.error("Required environment variables: SMTP_USERNAME, SMTP_PASSWORD")
        else:
            logger.info("Email service ready to send emails")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send an email using SMTP"""
        import logging
        logger = logging.getLogger(__name__)
        
        if not self.smtp_username or not self.smtp_password:
            logger.warning("Email credentials not configured. Skipping email send.")
            return False
        
        try:
            logger.info(f"Preparing to send email to {to_email} with subject: {subject}")
            
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Add text part
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            # Add HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            logger.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port}")
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return False
    
    def send_user_confirmation(self, user_email: str, form_data: Dict[str, Any]):
        """Send confirmation email to the user after form submission"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Sending user confirmation email to {user_email} for business: {form_data.get('business_name')}")
        
        subject = "Welcome to AIChatFlows – Your Setup Has Begun"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; color: #e0e0e0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(45deg, #00e676, #00b0ff); padding: 30px; text-align: center; border-radius: 10px; }}
                .header h1 {{ color: #ffffff; margin: 0; }}
                .content {{ background-color: #1a1a1a; padding: 30px; margin-top: 20px; border-radius: 10px; }}
                .content p {{ line-height: 1.6; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #00e676; color: #000; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #888; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to AIChatFlows!</h1>
                </div>
                <div class="content">
                    <p>Hi {form_data.get('business_name')},</p>
                    
                    <p>Thank you for joining AIChatFlows! We've received your submission and our team is already working on setting up your AI-powered chat automation.</p>
                    
                    <p><strong>What happens next?</strong></p>
                    <ul>
                        <li>Our team will begin setting up your automation within 24-48 hours</li>
                        <li>You'll receive an email once your system is ready to go live</li>
                        <li>We'll include training materials and best practices for your specific business</li>
                    </ul>
                    
                    <p><strong>Your Selected Plan:</strong> {form_data.get('plan')} Plan</p>
                    
                    <p>If you have any questions in the meantime, feel free to reach out to us at eliascolon23@gmail.com</p>
                    
                    <a href="https://aichatflows.com" class="button">Visit Our Website</a>
                </div>
                <div class="footer">
                    <p>© 2025 AIChatFlows. All rights reserved.</p>
                    <p>Your information is secure and encrypted.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to AIChatFlows!
        
        Hi {form_data.get('business_name')},
        
        Thank you for joining AIChatFlows! We've received your submission and our team is already working on setting up your AI-powered chat automation.
        
        What happens next?
        - Our team will begin setting up your automation within 24-48 hours
        - You'll receive an email once your system is ready to go live
        - We'll include training materials and best practices for your specific business
        
        Your Selected Plan: {form_data.get('plan')} Plan
        
        If you have any questions in the meantime, feel free to reach out to us at eliascolon23@gmail.com
        
        Best regards,
        The AIChatFlows Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_admin_notification(self, form_data: Dict[str, Any]):
        """Send notification email to admin with all form details"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Sending admin notification email for new signup: {form_data.get('business_name')} ({form_data.get('plan')} Plan)")
        
        subject = f"🚀 New Signup Submitted on AIChatFlows - {form_data.get('business_name')}"
        
        # Helper function to format timestamp
        timestamp = form_data.get('submission_timestamp', '')
        if timestamp:
            try:
                from datetime import datetime
                if 'T' in timestamp:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                else:
                    formatted_timestamp = timestamp
            except:
                formatted_timestamp = timestamp
        else:
            formatted_timestamp = 'N/A'
        
        # Helper function to format boolean values
        def format_boolean(value):
            if isinstance(value, bool):
                return "Yes" if value else "No"
            return value
        
        # Helper function to display non-empty values
        def get_value(key, default="Not provided"):
            value = form_data.get(key)
            if value is None or value == "" or value == "null":
                return default
            return value
        
        # Helper function to detect if a file URL is an image
        def is_image_file(file_url):
            if not file_url:
                return False
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
            return any(file_url.lower().endswith(ext) for ext in image_extensions)
        
        # Helper function to get file name from URL
        def get_filename_from_url(file_url):
            if not file_url:
                return "File"
            return file_url.split('/')[-1]
        
        # Helper function to create file display HTML
        def create_file_display(file_url, file_label):
            if not file_url:
                return f"<div class=\"detail-item\"><strong>• {file_label}:</strong> Not provided</div>"
            
            filename = get_filename_from_url(file_url)
            
            if is_image_file(file_url):
                return f"""
                    <div class="detail-item">
                        <strong>• {file_label}:</strong><br>
                        <div style="margin-top: 10px;">
                            <img src="{file_url}" alt="Preview of {filename}" style="max-width: 200px; max-height: 150px; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 5px; display: block;" onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
                            <div style="display: none; padding: 10px; background-color: #f0f0f0; border: 1px solid #ddd; border-radius: 4px; margin-bottom: 5px; color: #666; font-size: 0.9em;">
                                📷 Image preview unavailable - click link below to view
                            </div>
                            <a href="{file_url}" target="_blank" style="color: #00e676; text-decoration: none; font-size: 0.9em; font-weight: bold;">📎 View {filename}</a>
                        </div>
                    </div>"""
            else:
                return f"""
                    <div class="detail-item">
                        <strong>• {file_label}:</strong><br>
                        <div style="margin-top: 5px;">
                            <a href="{file_url}" target="_blank" style="color: #ffffff; text-decoration: none; padding: 8px 15px; background-color: #00e676; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 0.9em;">
                                📄 View File: {filename}
                            </a>
                        </div>
                    </div>"""
        
        # Helper function for text version file display
        def create_file_text(file_url, file_label):
            if not file_url:
                return f"• {file_label}: Not provided"
            
            filename = get_filename_from_url(file_url)
            if is_image_file(file_url):
                return f"• {file_label}: {filename} (Image) - {file_url}"
            else:
                return f"• {file_label}: {filename} - {file_url}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #00e676; color: #000; padding: 20px; text-align: center; }}
                .content {{ background-color: #fff; padding: 30px; margin-top: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .field {{ margin-bottom: 15px; }}
                .field-label {{ font-weight: bold; color: #333; }}
                .field-value {{ color: #666; margin-left: 10px; }}
                .highlight {{ background-color: #ffeb3b; padding: 2px 5px; }}
                .section {{ margin-bottom: 30px; }}
                .section h3 {{ color: #00e676; border-bottom: 2px solid #00e676; padding-bottom: 5px; margin-bottom: 15px; }}
                .form-details {{ background-color: #f9f9f9; padding: 20px; border-radius: 5px; margin-top: 20px; }}
                .form-details h3 {{ color: #333; margin-bottom: 15px; }}
                .detail-item {{ margin-bottom: 8px; }}
                .detail-item strong {{ color: #333; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New AIChatFlows Signup!</h1>
                </div>
                <div class="content">
                    <div class="section">
                        <h2>Business Summary</h2>
                        <div class="field">
                            <span class="field-label">Business Name:</span>
                            <span class="field-value">{form_data.get('business_name')}</span>
                        </div>
                        <div class="field">
                            <span class="field-label">Plan Selected:</span>
                            <span class="field-value highlight">{form_data.get('plan')} Plan</span>
                        </div>
                        <div class="field">
                            <span class="field-label">Contact Email:</span>
                            <span class="field-value">{form_data.get('contact_email')}</span>
                        </div>
                        <div class="field">
                            <span class="field-label">Submission Time:</span>
                            <span class="field-value">{formatted_timestamp}</span>
                        </div>
                    </div>
                    
                    <div class="form-details">
                        <h3>📋 Full Form Submission</h3>
                        
                        <div class="section">
                            <h3>Business Information</h3>
                            <div class="detail-item"><strong>• Business Name:</strong> {get_value('business_name')}</div>
                            <div class="detail-item"><strong>• Instagram Handle:</strong> {get_value('instagram_handle')}</div>
                            <div class="detail-item"><strong>• Other Platforms:</strong> {get_value('other_platforms')}</div>
                            <div class="detail-item"><strong>• Business Type:</strong> {get_value('business_type')}</div>"""
        
        # Add other business type if specified
        if form_data.get('business_type') == 'Other' and form_data.get('other_business_type'):
            html_content += f"""
                            <div class="detail-item"><strong>• Specified Business Type:</strong> {get_value('other_business_type')}</div>"""
        
        html_content += f"""
                            <div class="detail-item"><strong>• Product/Service Description:</strong> {get_value('product_service_description')}</div>
                            <div class="detail-item"><strong>• Common Customer Questions:</strong> {get_value('common_customer_question')}</div>
                        </div>
                        
                        <div class="section">
                            <h3>Delivery & Pickup</h3>
                            <div class="detail-item"><strong>• Delivery or Pickup:</strong> {get_value('delivery_pickup')}</div>"""
        
        # Show delivery services if applicable
        if form_data.get('delivery_pickup') in ['Delivery', 'Both']:
            if form_data.get('delivery_services'):
                html_content += f"""
                            <div class="detail-item"><strong>• Delivery Services:</strong> {get_value('delivery_services')}</div>"""
            if form_data.get('delivery_other'):
                html_content += f"""
                            <div class="detail-item"><strong>• Other Delivery Service:</strong> {get_value('delivery_other')}</div>"""
        
        # Show pickup details if applicable
        if form_data.get('delivery_pickup') in ['Pickup', 'Both']:
            if form_data.get('pickup_method'):
                html_content += f"""
                            <div class="detail-item"><strong>• Pickup Method:</strong> {get_value('pickup_method')}</div>"""
            if form_data.get('pickup_details'):
                html_content += f"""
                            <div class="detail-item"><strong>• Pickup Details:</strong> {get_value('pickup_details')}</div>"""
        
        html_content += f"""
                        </div>
                        
                        <div class="section">
                            <h3>Menu & Content</h3>
                            <div class="detail-item"><strong>• Menu Text:</strong> {get_value('menu_text')}</div>
                            {create_file_display(form_data.get('menu_upload'), 'Uploaded Menu')}
                            {create_file_display(form_data.get('additional_docs'), 'Additional Documents')}
                            <div class="detail-item"><strong>• Has FAQs:</strong> {format_boolean(form_data.get('has_faqs'))}</div>"""
        
        if form_data.get('has_faqs'):
            html_content += f"""
                            {create_file_display(form_data.get('faq_upload'), 'FAQ Document')}"""
        
        html_content += f"""
                        </div>
                        
                        <div class="section">
                            <h3>Setup & Credentials</h3>
                            <div class="detail-item"><strong>• Plan:</strong> {get_value('plan')}</div>
                            <div class="detail-item"><strong>• Submission Method:</strong> {get_value('submission_method')}</div>
                            <div class="detail-item"><strong>• Credential Handling:</strong> {get_value('credentials_handling', 'Standard processing')}</div>"""
        
        # Show login fields only if submitting through the page
        if form_data.get('submission_method') == 'Submit through this page':
            html_content += f"""
                            <div class="detail-item"><strong>• Instagram Username:</strong> {get_value('instagram_email')}</div>
                            <div class="detail-item"><strong>• Instagram Password:</strong> {"Provided" if form_data.get('instagram_password') else "Not provided"}</div>"""
            
            if form_data.get('plan') == 'Pro':
                html_content += f"""
                            <div class="detail-item"><strong>• Facebook Username:</strong> {get_value('facebook_email')}</div>
                            <div class="detail-item"><strong>• Facebook Password:</strong> {"Provided" if form_data.get('facebook_password') else "Not provided"}</div>"""
        
        html_content += f"""
                        </div>
                        
                        <div class="section">
                            <h3>Legal Confirmations</h3>
                            <div class="detail-item"><strong>• Consent to Share:</strong> {format_boolean(form_data.get('consent_to_share'))}</div>
                            <div class="detail-item"><strong>• Confirm Accurate:</strong> {format_boolean(form_data.get('confirm_accurate'))}</div>
                            <div class="detail-item"><strong>• Consent Automation:</strong> {format_boolean(form_data.get('consent_automation'))}</div>
                        </div>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        New AIChatFlows Signup!
        
        Business Summary:
        Business Name: {form_data.get('business_name')}
        Plan Selected: {form_data.get('plan')} Plan
        Contact Email: {form_data.get('contact_email')}
        Submission Time: {formatted_timestamp}
        
        📋 Full Form Submission:
        
        Business Information:
        • Business Name: {get_value('business_name')}
        • Instagram Handle: {get_value('instagram_handle')}
        • Other Platforms: {get_value('other_platforms')}
        • Business Type: {get_value('business_type')}"""
        
        # Add other business type if specified
        if form_data.get('business_type') == 'Other' and form_data.get('other_business_type'):
            text_content += f"""
        • Specified Business Type: {get_value('other_business_type')}"""
        
        text_content += f"""
        • Product/Service Description: {get_value('product_service_description')}
        • Common Customer Questions: {get_value('common_customer_question')}
        
        Delivery & Pickup:
        • Delivery or Pickup: {get_value('delivery_pickup')}"""
        
        # Show delivery services if applicable
        if form_data.get('delivery_pickup') in ['Delivery', 'Both']:
            if form_data.get('delivery_services'):
                text_content += f"""
        • Delivery Services: {get_value('delivery_services')}"""
            if form_data.get('delivery_other'):
                text_content += f"""
        • Other Delivery Service: {get_value('delivery_other')}"""
        
        # Show pickup details if applicable
        if form_data.get('delivery_pickup') in ['Pickup', 'Both']:
            if form_data.get('pickup_method'):
                text_content += f"""
        • Pickup Method: {get_value('pickup_method')}"""
            if form_data.get('pickup_details'):
                text_content += f"""
        • Pickup Details: {get_value('pickup_details')}"""
        
        text_content += f"""
        
        Menu & Content:
        • Menu Text: {get_value('menu_text')}
        {create_file_text(form_data.get('menu_upload'), 'Uploaded Menu')}
        {create_file_text(form_data.get('additional_docs'), 'Additional Documents')}
        • Has FAQs: {format_boolean(form_data.get('has_faqs'))}"""
        
        if form_data.get('has_faqs'):
            text_content += f"""
        {create_file_text(form_data.get('faq_upload'), 'FAQ Document')}"""
        
        text_content += f"""
        
        Setup & Credentials:
        • Plan: {get_value('plan')}
        • Submission Method: {get_value('submission_method')}
        • Credential Handling: {get_value('credentials_handling', 'Standard processing')}"""
        
        # Show login fields only if submitting through the page
        if form_data.get('submission_method') == 'Submit through this page':
            text_content += f"""
        • Instagram Username: {get_value('instagram_email')}
        • Instagram Password: {"Provided" if form_data.get('instagram_password') else "Not provided"}"""
            
            if form_data.get('plan') == 'Pro':
                text_content += f"""
        • Facebook Username: {get_value('facebook_email')}
        • Facebook Password: {"Provided" if form_data.get('facebook_password') else "Not provided"}"""
        
        text_content += f"""
        
        Legal Confirmations:
        • Consent to Share: {format_boolean(form_data.get('consent_to_share'))}
        • Confirm Accurate: {format_boolean(form_data.get('confirm_accurate'))}
        • Consent Automation: {format_boolean(form_data.get('consent_automation'))}
        """
        
        return self.send_email(self.admin_email, subject, html_content, text_content)
    
    def send_secure_credentials(self, user_email: str, form_data: Dict[str, Any]):
        """Send login credentials via secure email separately from main notification"""
        subject = "🔐 AIChatFlows - Your Login Credentials (Secure)"
        
        # Extract only the login credentials
        credentials = {}
        credential_fields = [
            'instagram_email', 'instagram_password',
            'facebook_email', 'facebook_password',
            'other_platform_credentials'
        ]
        
        for field in credential_fields:
            if form_data.get(field):
                credentials[field] = form_data[field]
        
        if not credentials:
            return True  # No credentials to send
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; color: #e0e0e0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(45deg, #ff6b6b, #feca57); padding: 30px; text-align: center; border-radius: 10px; }}
                .header h1 {{ color: #ffffff; margin: 0; }}
                .content {{ background-color: #1a1a1a; padding: 30px; margin-top: 20px; border-radius: 10px; }}
                .content p {{ line-height: 1.6; }}
                .credential-block {{ background-color: #2a2a2a; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #00e676; }}
                .credential-label {{ font-weight: bold; color: #00e676; }}
                .credential-value {{ color: #ffffff; font-family: monospace; }}
                .security-notice {{ background-color: #ff6b6b; color: #ffffff; padding: 15px; border-radius: 8px; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #888; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Your Login Credentials</h1>
                </div>
                <div class="content">
                    <p>Hi {form_data.get('business_name')},</p>
                    
                    <p>This email contains your social media login credentials for AIChatFlows setup. This information is sent via encrypted email and is not stored on our servers.</p>
                    
                    <p><strong>Plan:</strong> {form_data.get('plan')} Plan</p>
                    
                    <div class="credential-block">
                        <h3>Your Login Credentials:</h3>
        """
        
        # Add credentials to email
        for field, value in credentials.items():
            if field == 'other_platform_credentials':
                platform = 'Other Platforms'
                field_type = 'Credentials'
            else:
                platform = field.replace('_email', '').replace('_password', '').title()
                field_type = 'Username' if 'email' in field else 'Password'
            
            html_content += f"""
                        <div style="margin-bottom: 10px;">
                            <span class="credential-label">{platform} {field_type}:</span><br>
                            <span class="credential-value">{value}</span>
                        </div>
            """
        
        html_content += f"""
                    </div>
                    
                    <div class="security-notice">
                        <strong>🔒 Security Notice:</strong><br>
                        • This email will be automatically deleted from our systems within 24 hours<br>
                        • Your credentials are never stored permanently on our servers<br>
                        • We recommend changing your passwords after setup is complete<br>
                        • If you have any security concerns, contact us immediately
                    </div>
                    
                    <p>Our team will use these credentials only for the initial setup of your automation system. Once setup is complete, we'll notify you and you can change your passwords if desired.</p>
                    
                    <p>If you have any questions, contact us at eliascolon23@gmail.com</p>
                </div>
                <div class="footer">
                    <p>© 2025 AIChatFlows. All rights reserved.</p>
                    <p>This email contains sensitive information - please handle securely.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        🔐 Your AIChatFlows Login Credentials
        
        Hi {form_data.get('business_name')},
        
        This email contains your social media login credentials for AIChatFlows setup.
        
        Plan: {form_data.get('plan')} Plan
        
        LOGIN CREDENTIALS:
        """
        
        for field, value in credentials.items():
            if field == 'other_platform_credentials':
                platform = 'Other Platforms'
                field_type = 'Credentials'
            else:
                platform = field.replace('_email', '').replace('_password', '').title()
                field_type = 'Username' if 'email' in field else 'Password'
            text_content += f"\\n{platform} {field_type}: {value}"
        
        text_content += f"""
        
        🔒 SECURITY NOTICE:
        • This email will be automatically deleted from our systems within 24 hours
        • Your credentials are never stored permanently on our servers
        • We recommend changing your passwords after setup is complete
        • If you have any security concerns, contact us immediately
        
        Our team will use these credentials only for the initial setup of your automation system.
        
        Best regards,
        The AIChatFlows Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_payment_confirmation(self, user_email: str, business_name: str, plan: str):
        """Send final payment confirmation email to user after successful payment"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Sending payment confirmation email to {user_email} for business: {business_name} ({plan} Plan)")
        
        subject = "🎉 You're all set – Welcome to AI Chat Flows"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #0a0a0a; color: #e0e0e0; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(45deg, #00e676, #00b0ff); padding: 30px; text-align: center; border-radius: 10px; }}
                .header h1 {{ color: #ffffff; margin: 0; font-size: 2.2rem; }}
                .content {{ background-color: #1a1a1a; padding: 30px; margin-top: 20px; border-radius: 10px; }}
                .content p {{ line-height: 1.6; }}
                .success-badge {{ background: #00e676; color: #000; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; font-weight: bold; }}
                .next-steps {{ background: rgba(0, 230, 118, 0.1); padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .next-steps h3 {{ color: #00e676; margin-top: 0; }}
                .next-steps ul {{ padding-left: 20px; }}
                .next-steps li {{ margin-bottom: 8px; }}
                .button {{ display: inline-block; padding: 12px 30px; background: #00e676; color: #000; text-decoration: none; border-radius: 50px; font-weight: bold; margin-top: 20px; }}
                .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #888; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 Welcome to AIChatFlows!</h1>
                </div>
                <div class="content">
                    <div class="success-badge">
                        ✅ Payment Confirmed & Setup Initiated
                    </div>
                    
                    <p>Hi {business_name},</p>
                    
                    <p>Congratulations! Your payment has been successfully processed and your AI chat automation setup is now officially underway.</p>
                    
                    <p><strong>Your Plan:</strong> {plan} Plan</p>
                    
                    <div class="next-steps">
                        <h3>🚀 What Happens Next</h3>
                        <ul>
                            <li><strong>Within 24-48 hours:</strong> Our team will begin configuring your AI system with your business information</li>
                            <li><strong>Setup completion:</strong> You'll receive login credentials and access to your automation dashboard</li>
                            <li><strong>Training materials:</strong> Personalized guides and best practices for your specific business</li>
                            <li><strong>Go-live support:</strong> We'll be available to help you launch your first automated conversations</li>
                        </ul>
                    </div>
                    
                    <p>Our team is already working on your setup. You'll receive another email within the next 1-2 business days with your login details and next steps.</p>
                    
                    <p>Thank you for choosing AIChatFlows to automate your customer conversations!</p>
                    
                    <p>Questions? Reply to this email or contact us at eliascolon23@gmail.com</p>
                    
                    <a href="https://aichatflows.com" class="button">Visit Our Website</a>
                </div>
                <div class="footer">
                    <p>© 2025 AIChatFlows. All rights reserved.</p>
                    <p>Your AI chat automation journey starts now!</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        🎉 Welcome to AIChatFlows!
        
        Hi {business_name},
        
        Congratulations! Your payment has been successfully processed and your AI chat automation setup is now officially underway.
        
        Your Plan: {plan} Plan
        
        🚀 What Happens Next:
        - Within 24-48 hours: Our team will begin configuring your AI system with your business information
        - Setup completion: You'll receive login credentials and access to your automation dashboard
        - Training materials: Personalized guides and best practices for your specific business
        - Go-live support: We'll be available to help you launch your first automated conversations
        
        Our team is already working on your setup. You'll receive another email within the next 1-2 business days with your login details and next steps.
        
        Thank you for choosing AIChatFlows to automate your customer conversations!
        
        Questions? Reply to this email or contact us at eliascolon23@gmail.com
        
        Best regards,
        The AIChatFlows Team
        """
        
        return self.send_email(user_email, subject, html_content, text_content)
    
    def send_admin_payment_confirmation(self, business_name: str, plan: str, user_email: str):
        """Send admin notification that form + payment were both completed"""
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Sending admin payment confirmation for completed client: {business_name} ({plan} Plan) - {user_email}")
        
        subject = "✅ New Client Submission + Payment Completed"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4caf50; color: #fff; padding: 20px; text-align: center; }}
                .content {{ background-color: #fff; padding: 30px; margin-top: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
                .success-badge {{ background: #4caf50; color: #fff; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0; font-weight: bold; }}
                .field {{ margin-bottom: 15px; }}
                .field-label {{ font-weight: bold; color: #333; }}
                .field-value {{ color: #666; margin-left: 10px; }}
                .highlight {{ background-color: #ffeb3b; padding: 2px 5px; }}
                .actions {{ background-color: #e3f2fd; padding: 20px; border-radius: 8px; margin-top: 20px; }}
                .actions h3 {{ color: #1976d2; margin-top: 0; }}
                .actions ul {{ padding-left: 20px; }}
                .actions li {{ margin-bottom: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Payment Confirmed!</h1>
                </div>
                <div class="content">
                    <div class="success-badge">
                        🎉 COMPLETE: Form Submission + Payment Processed
                    </div>
                    
                    <h2>Client Successfully Onboarded</h2>
                    
                    <div class="field">
                        <span class="field-label">Business Name:</span>
                        <span class="field-value">{business_name}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Plan Purchased:</span>
                        <span class="field-value highlight">{plan} Plan</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Client Email:</span>
                        <span class="field-value">{user_email}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Payment Status:</span>
                        <span class="field-value" style="color: #4caf50; font-weight: bold;">✅ CONFIRMED</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Form Submission:</span>
                        <span class="field-value" style="color: #4caf50; font-weight: bold;">✅ COMPLETED</span>
                    </div>
                    
                    <div class="actions">
                        <h3>🚀 Next Actions Required</h3>
                        <ul>
                            <li>Review client's form submission in the /submissions/ directory</li>
                            <li>Begin AI system configuration within 24-48 hours</li>
                            <li>Prepare login credentials and dashboard access</li>
                            <li>Send setup completion email when ready</li>
                        </ul>
                    </div>
                    
                    <p><strong>Status:</strong> Client has successfully completed both onboarding form and payment. Ready for system setup.</p>
                    
                    <p>This client is now a confirmed, paying customer and should be prioritized for setup.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        ✅ New Client Submission + Payment Completed
        
        🎉 COMPLETE: Form Submission + Payment Processed
        
        Client Successfully Onboarded:
        
        Business Name: {business_name}
        Plan Purchased: {plan} Plan
        Client Email: {user_email}
        Payment Status: ✅ CONFIRMED
        Form Submission: ✅ COMPLETED
        
        🚀 Next Actions Required:
        - Review client's form submission in the /submissions/ directory
        - Begin AI system configuration within 24-48 hours
        - Prepare login credentials and dashboard access
        - Send setup completion email when ready
        
        Status: Client has successfully completed both onboarding form and payment. Ready for system setup.
        
        This client is now a confirmed, paying customer and should be prioritized for setup.
        """
        
        return self.send_email(self.admin_email, subject, html_content, text_content)