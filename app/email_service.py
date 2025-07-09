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
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.admin_email = 'eliascolon23@gmail.com'
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@aichatflows.com')
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
        """Send an email using SMTP"""
        if not self.smtp_username or not self.smtp_password:
            print("Email credentials not configured. Skipping email send.")
            return False
        
        try:
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
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    def send_user_confirmation(self, user_email: str, form_data: Dict[str, Any]):
        """Send confirmation email to the user"""
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
                    <p>© 2024 AIChatFlows. All rights reserved.</p>
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
        subject = f"🚀 New Signup Submitted on AIChatFlows - {form_data.get('business_name')}"
        
        # Format form data for email
        formatted_data = json.dumps(form_data, indent=2, default=str)
        
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
                pre {{ background-color: #f0f0f0; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                .highlight {{ background-color: #ffeb3b; padding: 2px 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>New AIChatFlows Signup!</h1>
                </div>
                <div class="content">
                    <h2>Business Information</h2>
                    <div class="field">
                        <span class="field-label">Business Name:</span>
                        <span class="field-value">{form_data.get('business_name')}</span>
                    </div>
                    <div class="field">
                        <span class="field-label">Instagram Handle:</span>
                        <span class="field-value">{form_data.get('instagram_handle')}</span>
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
                        <span class="field-value">{form_data.get('submission_timestamp')}</span>
                    </div>
                    
                    <h2>Complete Form Data</h2>
                    <pre>{formatted_data}</pre>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        New AIChatFlows Signup!
        
        Business Name: {form_data.get('business_name')}
        Instagram Handle: {form_data.get('instagram_handle')}
        Plan Selected: {form_data.get('plan')} Plan
        Contact Email: {form_data.get('contact_email')}
        Submission Time: {form_data.get('submission_timestamp')}
        
        Complete Form Data:
        {formatted_data}
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
                    <p>© 2024 AIChatFlows. All rights reserved.</p>
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
        """Send final payment confirmation email to user"""
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
                    <p>© 2024 AIChatFlows. All rights reserved.</p>
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