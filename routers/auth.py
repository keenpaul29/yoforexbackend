import logging
import re
import os
import random
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

import requests
import phonenumbers
from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, validator
from pydantic_core import PydanticCustomError
from passlib.context import CryptContext
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from utils.db import get_db
from models import User

# Load environment variables
load_dotenv()

# Logger
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# API router for authentication
router = APIRouter(prefix="/auth", tags=["auth"])

# WATI (WhatsApp) configuration
WATI_API_ENDPOINT = os.getenv("WATI_API_ENDPOINT")
WATI_ACCESS_TOKEN = os.getenv("WATI_ACCESS_TOKEN")

# --- JWT Helpers ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        payload = verify_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    user = db.query(User).filter(User.email == sub).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

# --- Schemas ---
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

    @validator('phone')
    def validate_phone(cls, v):
        if not re.match(r'^\+\d{10,15}$', v):
            raise PydanticCustomError('phone.format', 'Phone must be in E.164 format (e.g. +12345678901)')
        try:
            num = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(num):
                raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        except phonenumbers.NumberParseException:
            raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        return phonenumbers.format_number(num, phonenumbers.PhoneNumberFormat.E164)

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise PydanticCustomError('password.length', 'Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise PydanticCustomError('password.uppercase', 'Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise PydanticCustomError('password.lowercase', 'Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise PydanticCustomError('password.digit', 'Password must contain at least one digit')
        if not re.search(r'[^A-Za-z0-9]', v):
            raise PydanticCustomError('password.special', 'Password must contain at least one special character')
        return v

class OTPRequest(BaseModel):
    phone: str

    @validator('phone')
    def validate_phone_otp(cls, v):
        try:
            pn = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        if not phonenumbers.is_valid_number(pn):
            raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

    @validator('phone')
    def validate_phone_verify(cls, v):
        if not re.match(r'^\+\d{10,15}$', v):
            raise PydanticCustomError('phone.format', 'Phone must be in E.164 format')
        return v

    @validator('otp')
    def validate_otp_length(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise PydanticCustomError('otp.format', 'OTP must be exactly 4 digits')
        return v

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    phone: str

    @validator('phone')
    def validate_phone_reset(cls, v):
        try:
            pn = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        if not phonenumbers.is_valid_number(pn):
            raise PydanticCustomError('phone.invalid', 'Invalid phone number')
        return phonenumbers.format_number(pn, phonenumbers.PhoneNumberFormat.E164)

class PasswordReset(BaseModel):
    phone: str
    otp: str
    new_password: str

    @validator('otp')
    def validate_otp(cls, v):
        if not v.isdigit() or len(v) != 4:
            raise PydanticCustomError('otp.format', 'OTP must be exactly 4 digits')
        return v

    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise PydanticCustomError('password.length', 'Password must be at least 8 characters long')
        return v

class ProfileResponse(BaseModel):
    name: str
    email: EmailStr
    phone: str
    is_verified: bool
    attempts: int

# --- Helper: send_whatsapp_otp ---
def send_whatsapp_otp(phone: str, otp: str) -> Dict[str, Any]:
    url = f"{WATI_API_ENDPOINT}/api/v1/sendTemplateMessage?whatsappNumber={phone}"
    payload = {
        "template_name": "login_otp",
        "broadcast_name": f"login_otp_{datetime.utcnow().strftime('%d%m%Y%H%M%S')}",
        "parameters": [{"name": "1", "value": otp}]
    }
    headers = {
        "accept": "*/*",
        "Authorization": WATI_ACCESS_TOKEN,
        "Content-Type": "application/json-patch+json"
    }
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=10)
        logger.info(f"WATI responded {r.status_code}: {r.text}")
        r.raise_for_status()
    except requests.HTTPError:
        logger.error(f"WATI error {r.status_code}: {r.text}")
        raise HTTPException(status_code=502, detail=f"WATI API error: {r.status_code} {r.text}")
    except Exception as e:
        logger.exception("Failed to send OTP")
        raise HTTPException(status_code=502, detail=f"Error sending OTP: {e}")
    return r.json()

# --- Endpoints ---

@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup_endpoint(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User)\
        .filter((User.phone == payload.phone) | (User.email == payload.email))\
        .first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already registered and verified.")
    otp = str(random.randint(1000, 9999))
    expiry = datetime.utcnow() + timedelta(minutes=10)
    hashed = pwd_context.hash(payload.password)
    if not existing:
        user = User(
            name=payload.name,
            email=payload.email,
            phone=payload.phone,
            password_hash=hashed,
            is_verified=False,
            otp_code=otp,
            otp_expiry=expiry,
            attempts=0
        )
        db.add(user)
    else:
        existing.name = payload.name
        existing.email = payload.email
        existing.phone = payload.phone
        existing.password_hash = hashed
        existing.otp_code = otp
        existing.otp_expiry = expiry
        existing.attempts = 0
    db.commit()
    send_whatsapp_otp(payload.phone, otp)
    return {"status": "otp_sent"}

@router.post("/verify-signup-otp")
def verify_signup_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if user.is_verified:
        return {"status": "already_verified"}
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    user.attempts = 0
    db.commit()
    return {"status": "verified"}

@router.post("/login/email")
def login_email(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account not verified")
    token = create_access_token({"sub": user.email})
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=False,
        samesite="none",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {"status": "login_successful"}

@router.post("/login/request-otp")
def request_login_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Phone not registered.")
    otp = str(random.randint(1000, 9999))
    expiry = datetime.utcnow() + timedelta(minutes=10)
    user.otp_code = otp
    user.otp_expiry = expiry
    user.attempts = 0
    db.commit()
    send_whatsapp_otp(payload.phone, otp)
    return {"status": "otp_sent"}

@router.post("/login/verify-otp")
def verify_login_otp(
    payload: OTPVerifyRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
    token = create_access_token({"sub": user.email})
    response.set_cookie(
        "access_token",
        token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return {"status": "login_successful"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"status": "logged_out"}

@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    otp = f"{random.randint(1000, 9999):04d}"
    expiry = datetime.utcnow() + timedelta(minutes=10)
    user.otp_code = otp
    user.otp_expiry = expiry
    user.attempts = 0
    db.commit()
    send_whatsapp_otp(payload.phone, otp)
    return {"status": "otp_sent"}

@router.post("/reset-password")
def reset_password(payload: PasswordReset, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user or not user.otp_expiry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or no OTP requested.")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP.")
    user.password_hash = pwd_context.hash(payload.new_password)
    user.otp_code = None
    user.otp_expiry = None
    user.attempts = 0
    db.commit()
    return {"status": "password_reset_successful"}

@router.get("/profile", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileResponse(
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        is_verified=current_user.is_verified,
        attempts=current_user.attempts
    )
