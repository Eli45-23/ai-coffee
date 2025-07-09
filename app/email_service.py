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