from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, Annotated, List
from bson import ObjectId
from datetime import datetime

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError('Invalid objectid')
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")

class User(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: EmailStr
    hashed_password: str
    full_name: str
    department: Optional[str] = None
    phone_number: Optional[str] = None
    emp_id: Optional[str] = None
    role: str = "employee"
    is_manager: bool = False
    is_hr: bool = False

class LeaveRequestCreate(BaseModel):
    start_date: str
    end_date: str
    leave_type: str
    reason: str
    manager_email: str

class LeaveRequest(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )
    
    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    employee_id: Optional[PyObjectId] = None
    manager_id: Optional[PyObjectId] = None
    start_date: str
    end_date: str
    leave_type: str
    reason: str
    manager_email: str
    status: str = "pending"
    is_action_taken: bool = False
    approver_id: Optional[PyObjectId] = None
    action_timestamp: Optional[str] = None
    created_at: Optional[str] = None
    # Enhanced approval tracking
    approval_logs: Optional[List[dict]] = []
    security_token: Optional[str] = None
    requires_hr_approval: bool = False

class LeaveActionRequest(BaseModel):
    manager_password: str
    comments: Optional[str] = None

class SecureLeaveActionRequest(BaseModel):
    action_token: str
    manager_password: str
    action: str  # "approved" or "rejected"
    comments: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "employee"
    department: str
    phone_number: Optional[str] = None
    emp_id: Optional[str] = None
