import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime, timedelta
import jwt
import json
from pathlib import Path
from typing import Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv("EMAIL_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_USER", "your-email@company.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASS", "your-app-password")
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
FRONTEND_BASE_URL = os.getenv("FRONTEND_BASE_URL", "http://localhost:5174")

def generate_action_token(leave_request_id: str, manager_id: str, expires_hours: int = 24) -> str:
    """Generate secure action token for email actions"""
    expiry = datetime.utcnow() + timedelta(hours=expires_hours)
    payload = {
        'leave_request_id': leave_request_id,
        'manager_id': manager_id,
        'exp': expiry,
        'iat': datetime.utcnow(),
        'type': 'leave_action'
    }
    
    secret_key = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
    return jwt.encode(payload, secret_key, algorithm='HS256')

def load_amp_template() -> str:
    """Load the AMP email template"""
    template_path = Path(__file__).parent / "templates" / "leave_action.amp.html"
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"AMP template not found at {template_path}")
        raise

def calculate_leave_days(from_date: str, to_date: str) -> int:
    """Calculate total leave days excluding weekends"""
    try:
        start = datetime.strptime(from_date, '%Y-%m-%d')
        end = datetime.strptime(to_date, '%Y-%m-%d')
        
        total_days = 0
        current = start
        while current <= end:
            # Skip weekends (Saturday=5, Sunday=6)
            if current.weekday() < 5:  
                total_days += 1
            current += timedelta(days=1)
        
        return max(total_days, 1)  # At least 1 day
    except:
        return 1

def render_amp_template(leave_data: Dict[str, Any]) -> str:
    """Render the AMP email template with leave data"""
    template = load_amp_template()
    
    # Generate secure action token
    action_token = generate_action_token(
        str(leave_data['_id']), 
        str(leave_data.get('manager_id', ''))
    )
    
    # Calculate leave days
    total_days = calculate_leave_days(
        leave_data['from_date'], 
        leave_data['to_date']
    )
    
    # Determine if urgent (leave starts within 3 days)
    try:
        from_date = datetime.strptime(leave_data['from_date'], '%Y-%m-%d')
        days_until_leave = (from_date - datetime.now()).days
        is_urgent = days_until_leave <= 3
    except:
        is_urgent = False
    
    # Format submitted date
    try:
        if 'created_at' in leave_data:
            submitted_at = datetime.fromisoformat(leave_data['created_at'].replace('Z', '+00:00'))
        else:
            submitted_at = datetime.now()
        formatted_submitted = submitted_at.strftime('%B %d, %Y at %I:%M %p')
    except:
        formatted_submitted = datetime.now().strftime('%B %d, %Y at %I:%M %p')
    
    # Prepare template variables
    template_vars = {
        'employee_name': leave_data.get('employee_name', 'Unknown Employee'),
        'employee_id': leave_data.get('employee_id', ''),
        'employee_email': leave_data.get('employee_email', ''),
        'department': leave_data.get('department', 'Unknown'),
        'phone_number': leave_data.get('phone_number', ''),
        'manager_email': leave_data.get('manager_email', ''),
        'leave_type': leave_data.get('leave_type', 'Leave'),
        'from_date': leave_data.get('from_date', ''),
        'to_date': leave_data.get('to_date', ''),
        'reason': leave_data.get('reason', ''),
        'submitted_at': formatted_submitted,
        'total_days': total_days,
        'is_urgent': is_urgent,
        'leave_request_id': str(leave_data['_id']),
        'action_token': action_token,
        'manager_id': str(leave_data.get('manager_id', '')),
        'api_base_url': API_BASE_URL,
        'dashboard_url': f"{FRONTEND_BASE_URL}/manager/dashboard",
        'all_requests_url': f"{FRONTEND_BASE_URL}/manager/pending-approvals",
        'employee_profile_url': f"{FRONTEND_BASE_URL}/employee/profile/{leave_data.get('employee_id', '')}",
        'unsubscribe_url': f"{FRONTEND_BASE_URL}/unsubscribe",
        'help_url': f"{FRONTEND_BASE_URL}/help",
        'company_url': f"{FRONTEND_BASE_URL}"
    }
    
    # Simple template variable replacement
    rendered_template = template
    for key, value in template_vars.items():
        placeholder = f"{{{{{key}}}}}"
        rendered_template = rendered_template.replace(placeholder, str(value))
    
    # Handle conditional sections for urgent badge
    if is_urgent:
        rendered_template = rendered_template.replace('{{#is_urgent}}', '').replace('{{/is_urgent}}', '')
    else:
        # Remove urgent badge section
        import re
        rendered_template = re.sub(r'{{#is_urgent}}.*?{{/is_urgent}}', '', rendered_template, flags=re.DOTALL)
    
    return rendered_template

def send_leave_action_email(leave_data: Dict[str, Any]) -> bool:
    """Send interactive AMP email to manager for leave approval"""
    try:
        # Render AMP template
        amp_html = render_amp_template(leave_data)
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"🚨 Leave Request - {leave_data.get('employee_name', 'Unknown')} ({leave_data.get('employee_id', '')})"
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = leave_data.get('manager_email', '')
        
        # Add custom headers for better email client support
        msg['X-Priority'] = '1'  # High priority
        msg['X-MSMail-Priority'] = 'High'
        msg['Importance'] = 'high'
        
        # Create plain text version
        text_content = f"""
        Leave Request - Action Required
        
        Employee: {leave_data.get('employee_name', 'Unknown')}
        Employee ID: {leave_data.get('employee_id', '')}
        Email: {leave_data.get('employee_email', '')}
        Department: {leave_data.get('department', '')}
        
        Leave Details:
        Type: {leave_data.get('leave_type', '')}
        From: {leave_data.get('from_date', '')}
        To: {leave_data.get('to_date', '')}
        Reason: {leave_data.get('reason', '')}
        
        To approve or reject this request, please use the interactive email or visit:
        {FRONTEND_BASE_URL}/manager/pending-approvals
        
        This is an automated message from Leave Management System.
        """
        
        # Create HTML fallback version
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%); color: white; padding: 30px; border-radius: 16px 16px 0 0; text-align: center;">
                <h1 style="margin: 0;">📋 Leave Request</h1>
                <p style="margin: 10px 0 0 0;">Action Required - Employee Leave Application</p>
            </div>
            
            <div style="border: 1px solid #e5e7eb; border-top: none; padding: 30px; border-radius: 0 0 16px 16px;">
                <h2 style="color: #1f2937; margin-top: 0;">Employee: {leave_data.get('employee_name', 'Unknown')}</h2>
                
                <div style="background: #f8fafc; padding: 20px; border-radius: 12px; border-left: 4px solid #3b82f6;">
                    <p><strong>Employee ID:</strong> {leave_data.get('employee_id', '')}</p>
                    <p><strong>Email:</strong> {leave_data.get('employee_email', '')}</p>
                    <p><strong>Department:</strong> {leave_data.get('department', '')}</p>
                    <p><strong>Leave Type:</strong> {leave_data.get('leave_type', '')}</p>
                    <p><strong>From Date:</strong> {leave_data.get('from_date', '')}</p>
                    <p><strong>To Date:</strong> {leave_data.get('to_date', '')}</p>
                    <p><strong>Reason:</strong> {leave_data.get('reason', '')}</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{FRONTEND_BASE_URL}/manager/pending-approvals" 
                       style="background: #10b981; color: white; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; margin: 0 8px; display: inline-block;">
                        ✅ APPROVE REQUEST
                    </a>
                    <a href="{FRONTEND_BASE_URL}/manager/pending-approvals" 
                       style="background: #ef4444; color: white; padding: 16px 32px; border-radius: 12px; text-decoration: none; font-weight: 600; margin: 0 8px; display: inline-block;">
                        ❌ REJECT REQUEST
                    </a>
                </div>
                
                <p style="text-align: center; color: #6b7280; font-size: 14px;">
                    Click the buttons above or visit your dashboard to process this leave request.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Attach parts
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        part3 = MIMEText(amp_html, 'html')
        
        # Set AMP content type
        part3.set_param('content-type', 'text/x-amp-html')
        
        msg.attach(part1)
        msg.attach(part2)
        msg.attach(part3)
        
        # Send email
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, leave_data.get('manager_email', ''), text)
        
        logger.info(f"AMP leave request email sent to {leave_data.get('manager_email', '')}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send AMP email: {str(e)}")
        return False

def send_notification_email(to_email: str, subject: str, message: str, is_html: bool = False) -> bool:
    """Send simple notification email"""
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if is_html:
            msg.attach(MIMEText(message, 'html'))
        else:
            msg.attach(MIMEText(message, 'plain'))
        
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, to_email, text)
        
        logger.info(f"Notification email sent to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send notification email: {str(e)}")
        return False

def notify_employee(leave_data: Dict[str, Any], action: str, comments: str = "") -> bool:
    """Send notification to employee about leave request action"""
    try:
        subject = f"Leave Request {action.title()} - {leave_data.get('leave_type', 'Leave')}"
        
        message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: {'#d1fae5' if action == 'approved' else '#fee2e2'}; border-radius: 12px; padding: 20px; text-align: center;">
                <h2 style="color: {'#065f46' if action == 'approved' else '#991b1b'}; margin: 0 0 16px 0;">
                    {'✅' if action == 'approved' else '❌'} Leave Request {action.title()}
                </h2>
                
                <p><strong>Leave Type:</strong> {leave_data.get('leave_type', '')}</p>
                <p><strong>Duration:</strong> {leave_data.get('from_date', '')} to {leave_data.get('to_date', '')}</p>
                
                {f'<div style="background: white; border-radius: 8px; padding: 16px; margin: 16px 0; text-align: left;"><strong>Manager Comments:</strong><br>{comments}</div>' if comments else ''}
                
                <p style="margin-top: 20px;">
                    <a href="{FRONTEND_BASE_URL}/employee/my-requests" 
                       style="background: #3b82f6; color: white; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: 600;">
                        View My Requests
                    </a>
                </p>
            </div>
        </body>
        </html>
        """
        
        return send_notification_email(
            leave_data.get('employee_email', ''), 
            subject, 
            message, 
            is_html=True
        )
        
    except Exception as e:
        logger.error(f"Failed to notify employee: {str(e)}")
        return False
