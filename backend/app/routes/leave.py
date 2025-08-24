from fastapi import APIRouter, HTTPException, Depends, Request, status, Form
from app.models.db import leaves_collection, users_collection
from app.models.schemas import LeaveRequestCreate, LeaveRequest, LeaveActionRequest, SecureLeaveActionRequest
from app.utils.auth import verify_token, verify_password, generate_secure_action_token, verify_secure_action_token, create_approval_log
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional, List
import jwt
import os

router = APIRouter()

# JWT secret for token verification
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")

@router.post("/submit")
def submit_leave(leave: LeaveRequestCreate, user_id: str = Depends(verify_token)):
    # Get user details
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Find manager by email
    manager = users_collection.find_one({"email": leave.manager_email})
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Create leave request
    leave_dict = leave.model_dump()
    leave_dict.update({
        "employee_id": ObjectId(user_id),
        "manager_id": ObjectId(manager["_id"]),
        "status": "pending",
        "is_action_taken": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "approval_logs": [],  # Initialize empty approval logs
        "requires_hr_approval": leave.leave_type.lower() in ["medical", "emergency", "extended"]  # Some leaves may require HR approval
    })
    
    result = leaves_collection.insert_one(leave_dict)
    leave_id = str(result.inserted_id)
    
    # Generate secure action token for the manager
    try:
        security_token = generate_secure_action_token(leave_id, str(manager["_id"]))
        # Update the leave request with the security token
        leaves_collection.update_one(
            {"_id": result.inserted_id},
            {"$set": {"security_token": security_token}}
        )
    except Exception as e:
        print(f"Warning: Failed to generate security token: {str(e)}")
        security_token = None
    
    # Prepare comprehensive data for AMP email
    amp_email_data = {
        "_id": result.inserted_id,
        "employee_name": user.get("full_name", user.get("username", "Unknown")),
        "employee_id": str(user.get("_id", "")),
        "employee_email": user.get("email", ""),
        "department": user.get("department", "Unknown"),
        "phone_number": user.get("phone", ""),
        "manager_id": str(manager["_id"]),
        "manager_email": manager.get("email", ""),
        "leave_type": leave.leave_type,
        "from_date": leave.from_date,
        "to_date": leave.to_date,
        "reason": leave.reason,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "security_token": security_token,  # Include secure token for AMP email
        "requires_hr_approval": leave.leave_type.lower() in ["medical", "emergency", "extended"]
    }
    
    # Send interactive AMP email to manager
    try:
        # email_sent = send_leave_action_email(amp_email_data)  # Temporarily disabled
        # if not email_sent:
        #     print("Warning: Failed to send AMP email to manager")
        print("Email functionality temporarily disabled for testing")
    except Exception as e:
        print(f"Email sending error: {str(e)}")
    
    return {"leave_request_id": str(result.inserted_id), "status": "pending"}

@router.get("/my-requests", response_model=List[dict])
def get_my_requests(user_id: str = Depends(verify_token)):
    leaves = list(leaves_collection.find({"employee_id": ObjectId(user_id)}))
    for leave in leaves:
        leave["_id"] = str(leave["_id"])
        leave["employee_id"] = str(leave["employee_id"])
        leave["manager_id"] = str(leave["manager_id"])
        if leave.get("approver_id"):
            leave["approver_id"] = str(leave["approver_id"])
    return leaves

@router.get("/pending-approvals", response_model=List[dict])
def get_pending_approvals(user_id: str = Depends(verify_token)):
    # Check if user is a manager
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user or not user.get("is_manager"):
        raise HTTPException(status_code=403, detail="Access denied. Manager role required.")
    
    leaves = list(leaves_collection.find({
        "manager_id": ObjectId(user_id), 
        "status": "pending",
        "is_action_taken": False
    }))
    
    for leave in leaves:
        leave["_id"] = str(leave["_id"])
        leave["employee_id"] = str(leave["employee_id"])
        leave["manager_id"] = str(leave["manager_id"])
        if leave.get("approver_id"):
            leave["approver_id"] = str(leave["approver_id"])
    return leaves

@router.post("/{leave_id}/approve")
def approve_leave(leave_id: str, action_data: LeaveActionRequest):
    return process_leave_action(leave_id, "approved", action_data.manager_password, action_data.comments)

@router.post("/{leave_id}/reject") 
def reject_leave(leave_id: str, action_data: LeaveActionRequest):
    return process_leave_action(leave_id, "rejected", action_data.manager_password, action_data.comments)

def process_leave_action(leave_id: str, action: str, password: str, comments: Optional[str] = None):
    # Find leave request
    leave = leaves_collection.find_one({"_id": ObjectId(leave_id)})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave.get("is_action_taken"):
        raise HTTPException(status_code=400, detail="Action already taken on this leave request")
    
    # Verify manager password
    manager = users_collection.find_one({"_id": ObjectId(leave["manager_id"])})
    if not manager or not verify_password(password, manager["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid manager password")
    
    # Get employee details for notification
    employee = users_collection.find_one({"_id": ObjectId(leave["employee_id"])})
    
    # Update leave status
    update_data = {
        "status": action,
        "is_action_taken": True,
        "approver_id": ObjectId(leave["manager_id"]),
        "action_timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if comments:
        update_data["comments"] = comments
    
    leaves_collection.update_one({"_id": ObjectId(leave_id)}, {"$set": update_data})
    
    # Prepare data for employee notification
    if employee:
        notification_data = {
            "employee_name": employee.get("full_name", employee.get("username", "Unknown")),
            "employee_email": employee.get("email", ""),
            "leave_type": leave.get("leave_type", "Leave"),
            "from_date": leave.get("from_date", ""),
            "to_date": leave.get("to_date", "")
        }
        
        # Notify employee about the decision
        try:
            # notify_employee(notification_data, action, comments or "")  # Temporarily disabled
            print(f"Employee notification temporarily disabled for testing - {action}")
        except Exception as e:
            print(f"Failed to notify employee: {str(e)}")
    
    return {
        "status": action,
        "message": f"Leave request {action} successfully.",
        "comments": comments
    }

# AMP Email Action Endpoints
@router.post("/amp/approve")
async def amp_approve_leave(
    token: str = Form(...),
    comments: Optional[str] = Form(None)
):
    """Handle AMP email approve action"""
    return process_amp_action(token, "approved", comments)

@router.post("/amp/reject")
async def amp_reject_leave(
    token: str = Form(...),
    comments: Optional[str] = Form(None)
):
    """Handle AMP email reject action"""
    return process_amp_action(token, "rejected", comments)

def process_amp_action(token: str, action: str, comments: Optional[str] = None):
    """Process AMP email actions with secure token verification"""
    try:
        # Verify and decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        leave_request_id = payload.get('leave_request_id')
        manager_id = payload.get('manager_id')
        
        if not leave_request_id or not manager_id:
            raise HTTPException(status_code=400, detail="Invalid token payload")
        
        # Find leave request
        leave = leaves_collection.find_one({"_id": ObjectId(leave_request_id)})
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        if leave.get("is_action_taken"):
            return {
                "success": False,
                "message": "Action already taken on this leave request",
                "status": leave.get("status")
            }
        
        # Verify manager
        manager = users_collection.find_one({"_id": ObjectId(manager_id)})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        # Get employee details
        employee = users_collection.find_one({"_id": ObjectId(leave["employee_id"])})
        
        # Update leave status
        update_data = {
            "status": action,
            "is_action_taken": True,
            "approver_id": ObjectId(manager_id),
            "action_timestamp": datetime.now(timezone.utc).isoformat(),
            "action_method": "amp_email"
        }
        
        if comments:
            update_data["comments"] = comments.strip()
        
        leaves_collection.update_one(
            {"_id": ObjectId(leave_request_id)}, 
            {"$set": update_data}
        )
        
        # Prepare employee notification data
        if employee:
            notification_data = {
                "employee_name": employee.get("full_name", employee.get("username", "Unknown")),
                "employee_email": employee.get("email", ""),
                "leave_type": leave.get("leave_type", "Leave"),
                "from_date": leave.get("from_date", ""),
                "to_date": leave.get("to_date", "")
            }
            
            # Send notification to employee
            try:
                # notify_employee(notification_data, action, comments or "")  # Temporarily disabled
                print(f"Employee notification temporarily disabled for testing - {action}")
            except Exception as e:
                print(f"Failed to notify employee: {str(e)}")
        
        return {
            "success": True,
            "message": f"Leave request {action} successfully via AMP email",
            "action": action,
            "leave_id": leave_request_id,
            "employee_name": employee.get("full_name", "Unknown") if employee else "Unknown",
            "comments": comments
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Action processing failed: {str(e)}")

@router.get("/amp/status/{token}")
def get_amp_action_status(token: str):
    """Check the status of a leave request from AMP email token"""
    try:
        # Verify and decode token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
        leave_request_id = payload.get('leave_request_id')
        
        if not leave_request_id:
            raise HTTPException(status_code=400, detail="Invalid token")
        
        # Find leave request
        leave = leaves_collection.find_one({"_id": ObjectId(leave_request_id)})
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Get employee details
        employee = users_collection.find_one({"_id": ObjectId(leave["employee_id"])})
        
        return {
            "leave_id": str(leave["_id"]),
            "employee_name": employee.get("full_name", "Unknown") if employee else "Unknown",
            "leave_type": leave.get("leave_type", "Leave"),
            "from_date": leave.get("from_date", ""),
            "to_date": leave.get("to_date", ""),
            "status": leave.get("status", "pending"),
            "is_action_taken": leave.get("is_action_taken", False),
            "comments": leave.get("comments", ""),
            "action_timestamp": leave.get("action_timestamp")
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=400, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=400, detail="Invalid token")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Status check failed: {str(e)}")

@router.post("/secure-approve/{leave_id}")
def secure_approve_leave(
    leave_id: str,
    request: Request,
    action_data: SecureLeaveActionRequest
):
    """Secure endpoint for approving/rejecting leave requests with enhanced authentication"""
    try:
        # Verify the leave request exists
        leave = leaves_collection.find_one({"_id": ObjectId(leave_id)})
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Verify the secure action token
        token_payload = verify_secure_action_token(action_data.action_token, leave_id)
        manager_id = token_payload.get("manager_id")
        
        # Get manager details
        manager = users_collection.find_one({"_id": ObjectId(manager_id)})
        if not manager:
            raise HTTPException(status_code=404, detail="Manager not found")
        
        # Verify manager password
        if not verify_password(action_data.manager_password, manager["hashed_password"]):
            raise HTTPException(status_code=401, detail="Invalid manager credentials")
        
        # Check if manager has permission to approve this request
        if not (manager.get("is_manager") or manager.get("is_hr")):
            raise HTTPException(status_code=403, detail="Insufficient permissions to approve leave")
        
        # Additional check: ensure manager is the designated approver
        if leave.get("manager_email") != manager.get("email") and not manager.get("is_hr"):
            raise HTTPException(status_code=403, detail="You are not authorized to approve this specific leave request")
        
        # Check if already processed
        if leave.get("is_action_taken", False):
            raise HTTPException(status_code=400, detail="This leave request has already been processed")
        
        # Validate action
        if action_data.action not in ["approved", "rejected"]:
            raise HTTPException(status_code=400, detail="Action must be 'approved' or 'rejected'")
        
        # Get client information for logging
        client_ip = request.client.host if request.client else "Unknown"
        user_agent = request.headers.get("user-agent", "Unknown")
        
        # Create detailed approval log
        approval_log = create_approval_log(
            action=action_data.action,
            manager_id=str(manager["_id"]),
            manager_email=manager["email"],
            comments=action_data.comments or "",
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Update leave request with secure approval
        update_data = {
            "status": action_data.action,
            "is_action_taken": True,
            "approver_id": ObjectId(manager_id),
            "action_timestamp": datetime.now(timezone.utc).isoformat(),
            "comments": action_data.comments or "",
            "$push": {"approval_logs": approval_log}  # Add to approval history
        }
        
        # Update the leave request
        result = leaves_collection.update_one(
            {"_id": ObjectId(leave_id)},
            update_data
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=500, detail="Failed to update leave request")
        
        # Get employee details for notification
        employee = users_collection.find_one({"_id": leave.get("employee_id")})
        
        # Prepare notification data (email functionality commented out for testing)
        notification_data = {
            "employee_email": employee.get("email", "") if employee else "",
            "employee_name": employee.get("full_name", "Unknown") if employee else "Unknown",
            "leave_type": leave.get("leave_type", "Leave"),
            "from_date": leave.get("start_date", ""),
            "to_date": leave.get("end_date", "")
        }
        
        # Send notification to employee (temporarily disabled)
        try:
            # notify_employee(notification_data, action_data.action, action_data.comments or "")
            print(f"Secure approval notification temporarily disabled - {action_data.action}")
        except Exception as e:
            print(f"Failed to notify employee: {str(e)}")
        
        return {
            "success": True,
            "message": f"Leave request {action_data.action} successfully with secure authentication",
            "leave_id": leave_id,
            "action": action_data.action,
            "approved_by": manager["full_name"],
            "approved_at": approval_log["timestamp"],
            "verification_level": "secure_token",
            "log_id": approval_log["log_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Secure approval failed: {str(e)}")

@router.get("/approval-logs/{leave_id}")
def get_approval_logs(leave_id: str, current_user=Depends(verify_token)):
    """Get detailed approval logs for a leave request"""
    try:
        leave = leaves_collection.find_one({"_id": ObjectId(leave_id)})
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Get current user details
        user = users_collection.find_one({"_id": ObjectId(current_user)})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if user has permission to view logs
        is_employee = str(leave.get("employee_id")) == current_user
        is_manager_or_hr = user.get("is_manager") or user.get("is_hr")
        
        if not (is_employee or is_manager_or_hr):
            raise HTTPException(status_code=403, detail="Insufficient permissions to view approval logs")
        
        approval_logs = leave.get("approval_logs", [])
        
        # Enhance logs with manager names
        enhanced_logs = []
        for log in approval_logs:
            manager = users_collection.find_one({"_id": ObjectId(log.get("manager_id", ""))})
            enhanced_log = log.copy()
            enhanced_log["manager_name"] = manager.get("full_name", "Unknown") if manager else "Unknown"
            enhanced_log["manager_department"] = manager.get("department", "Unknown") if manager else "Unknown"
            enhanced_logs.append(enhanced_log)
        
        return {
            "leave_id": leave_id,
            "current_status": leave.get("status", "pending"),
            "is_action_taken": leave.get("is_action_taken", False),
            "approval_logs": enhanced_logs,
            "total_actions": len(enhanced_logs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get approval logs: {str(e)}")

@router.post("/generate-action-token/{leave_id}")
def generate_action_token_endpoint(leave_id: str, current_user=Depends(verify_token)):
    """Generate a secure action token for a leave request (for testing/admin purposes)"""
    try:
        # Verify user is manager or HR
        user = users_collection.find_one({"_id": ObjectId(current_user)})
        if not user or not (user.get("is_manager") or user.get("is_hr")):
            raise HTTPException(status_code=403, detail="Only managers and HR can generate action tokens")
        
        # Verify leave request exists
        leave = leaves_collection.find_one({"_id": ObjectId(leave_id)})
        if not leave:
            raise HTTPException(status_code=404, detail="Leave request not found")
        
        # Generate secure token
        action_token = generate_secure_action_token(leave_id, current_user)
        
        return {
            "leave_id": leave_id,
            "action_token": action_token,
            "expires_in_hours": 48,
            "generated_for": user.get("full_name", "Unknown"),
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate action token: {str(e)}")
