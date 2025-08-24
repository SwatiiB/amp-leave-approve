from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from bson import ObjectId
from ..models.db import get_database
from ..utils.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/emails", tags=["emails"])

@router.get("/notifications")
async def get_email_notifications(
    current_user: dict = Depends(get_current_user),
    db = Depends(get_database)
):
    """Get email notifications for HR - leave requests sent via email"""
    try:
        # Check if user is HR
        if current_user.get("role") != "hr":
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Mock email notifications data
        # In real implementation, this would fetch from email service or database
        notifications = [
            {
                "id": 1,
                "subject": "Leave Request - John Doe (EMP001)",
                "from_employee": "John Doe",
                "employee_id": "EMP001",
                "leave_type": "Annual Leave",
                "from_date": "2024-01-15",
                "to_date": "2024-01-17",
                "reason": "Family vacation",
                "manager_email": "manager@company.com",
                "is_read": False,
                "received_at": "2024-01-10T09:30:00Z",
                "leave_request_id": "LR001"
            },
            {
                "id": 2,
                "subject": "Leave Request - Jane Smith (EMP002)",
                "from_employee": "Jane Smith", 
                "employee_id": "EMP002",
                "leave_type": "Sick Leave",
                "from_date": "2024-01-12",
                "to_date": "2024-01-12",
                "reason": "Medical appointment",
                "manager_email": "manager@company.com",
                "is_read": True,
                "received_at": "2024-01-09T14:15:00Z",
                "leave_request_id": "LR002"
            }
        ]
        
        return {"notifications": notifications}
        
    except Exception as e:
        logger.error(f"Error fetching email notifications: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/{email_id}/read")
async def mark_email_as_read(
    email_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Mark an email notification as read"""
    try:
        # Check if user is HR
        if current_user.get("role") != "hr":
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # In real implementation, update the email status in database
        logger.info(f"Email {email_id} marked as read by {current_user['emp_id']}")
        
        return {
            "success": True,
            "message": "Email marked as read"
        }
        
    except Exception as e:
        logger.error(f"Error marking email as read: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/send-action")
async def send_action_email(
    leave_request_id: str,
    action: str,
    comments: Optional[str] = "",
    current_user: dict = Depends(get_current_user)
):
    """Send email notification after approving/rejecting leave request"""
    try:
        # Check if user is HR
        if current_user.get("role") != "hr":
            raise HTTPException(status_code=403, detail="Access denied. HR role required.")
        
        # Validate action
        if action not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # In real implementation, send email to employee
        # TODO: Integrate with email service (SendGrid, AWS SES, etc.)
        logger.info(f"Action email sent for leave request {leave_request_id}: {action}")
        
        return {
            "success": True,
            "message": f"Email notification sent - leave request {action}"
        }
        
    except Exception as e:
        logger.error(f"Error sending action email: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/templates")
async def get_email_templates():
    """Get available email templates"""
    try:
        templates = {
            "approval_template": {
                "subject": "Leave Request Approved",
                "body": "Your leave request has been approved. Details: {details}"
            },
            "rejection_template": {
                "subject": "Leave Request Rejected", 
                "body": "Your leave request has been rejected. Reason: {reason}"
            }
        }
        
        return templates
        
    except Exception as e:
        logger.error(f"Error fetching email templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/process-action")
async def process_email_action(
    token: str,
    action: str
):
    """Process approve/reject action directly from email link"""
    try:
        # Validate action
        if action not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # In real implementation:
        # 1. Decode and validate the token
        # 2. Extract leave request ID from token
        # 3. Update leave request status
        # 4. Send confirmation email
        
        logger.info(f"Email action processed: {action}")
        
        return {
            "success": True,
            "message": f"Leave request {action} via email",
            "redirect_url": "/hr/dashboard"
        }
        
    except Exception as e:
        logger.error(f"Error processing email action: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
