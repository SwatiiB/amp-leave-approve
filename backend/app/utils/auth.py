from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
import secrets
import hashlib
from typing import Optional, Dict, Any
from datetime import timezone
from app.models.db import users_collection
from bson import ObjectId

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    return user_id

def generate_secure_action_token(leave_request_id: str, manager_id: str, action_type: str = "leave_approval") -> str:
    """Generate a cryptographically secure action token for leave approval/rejection"""
    # Create a unique payload
    timestamp = datetime.now(timezone.utc).isoformat()
    random_salt = secrets.token_hex(16)
    
    payload = {
        "leave_request_id": leave_request_id,
        "manager_id": manager_id,
        "action_type": action_type,
        "timestamp": timestamp,
        "salt": random_salt,
        "exp": datetime.utcnow() + timedelta(hours=48)  # Token expires in 48 hours
    }
    
    # Create secure token
    token = jwt.encode(payload, SECRET_KEY + random_salt, algorithm=ALGORITHM)
    
    # Additional security: create hash of token + leave_request_id
    security_hash = hashlib.sha256((token + leave_request_id).encode()).hexdigest()
    
    return f"{token}.{security_hash}"

def verify_secure_action_token(action_token: str, leave_request_id: str) -> Dict[str, Any]:
    """Verify and decode secure action token"""
    try:
        # Split token and hash
        if "." not in action_token:
            raise HTTPException(status_code=400, detail="Invalid action token format")
        
        token_part, provided_hash = action_token.rsplit(".", 1)
        
        # Verify hash integrity
        expected_hash = hashlib.sha256((token_part + leave_request_id).encode()).hexdigest()
        if not secrets.compare_digest(provided_hash, expected_hash):
            raise HTTPException(status_code=400, detail="Token integrity check failed")
        
        # First decode to get salt
        try:
            unverified_payload = jwt.get_unverified_claims(token_part)
            salt = unverified_payload.get("salt")
            if not salt:
                raise HTTPException(status_code=400, detail="Invalid token structure")
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid token structure")
        
        # Decode with salted secret
        payload = jwt.decode(token_part, SECRET_KEY + salt, algorithms=[ALGORITHM])
        
        # Verify leave request ID matches
        if payload.get("leave_request_id") != leave_request_id:
            raise HTTPException(status_code=400, detail="Token does not match leave request")
        
        return payload
        
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired action token")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Token verification failed: {str(e)}")

def create_approval_log(action: str, manager_id: str, manager_email: str, comments: str = "", 
                       ip_address: str = "", user_agent: str = "") -> Dict[str, Any]:
    """Create a detailed approval log entry"""
    return {
        "action": action,
        "manager_id": manager_id,
        "manager_email": manager_email,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "comments": comments or "",
        "ip_address": ip_address or "Unknown",
        "user_agent": user_agent or "Unknown",
        "verification_level": "secure_token",  # Indicates this was done via secure token
        "log_id": secrets.token_hex(8)  # Unique log entry ID
    }
