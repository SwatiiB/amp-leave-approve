from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.models.db import users_collection
from app.models.schemas import Token, UserCreate
from app.utils.auth import verify_password, get_password_hash, create_access_token
from bson import ObjectId
from datetime import timedelta
import os

router = APIRouter()

@router.post("/register")
def register_user(user_data: UserCreate):
    # Check if user already exists
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user document
    user_dict = {
        "email": user_data.email,
        "hashed_password": get_password_hash(user_data.password),
        "full_name": user_data.full_name,
        "role": user_data.role,
        "department": user_data.department,
        "phone_number": getattr(user_data, 'phone_number', None),
        "emp_id": getattr(user_data, 'emp_id', None),
        "is_manager": user_data.role == "manager",
        "is_hr": user_data.role == "hr"
    }
    
    result = users_collection.insert_one(user_dict)
    return {"user_id": str(result.inserted_id), "message": "User registered successfully"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Find user by email (form_data.username contains the email)
    user = users_collection.find_one({"email": form_data.username})
    
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    access_token = create_access_token(
        data={"sub": str(user["_id"]), "email": user["email"]},
        expires_delta=timedelta(minutes=60*24)
    )
    return {"access_token": access_token, "token_type": "bearer"}
