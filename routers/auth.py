# routers/auth.py
import logging
import re
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr, validator
from pydantic_core import PydanticCustomError
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
import random
import os
import requests
from passlib.context import CryptContext
from dotenv import load_dotenv
import phonenumbers

from utils.db import get_db
from models import User

# Setup
logger = logging.getLogger(__name__)
load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])

# WATI Configuration
WATI_API_ENDPOINT = os.getenv("WATI_API_ENDPOINT")
WATI_ACCESS_TOKEN = os.getenv("WATI_ACCESS_TOKEN")

# Schemas
JSON = Dict[str, Any]

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
            # None means “expect the +COUNTRY code” in the string
            pn = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            raise ValueError('Invalid phone number')

        if not phonenumbers.is_valid_number(pn):
            raise ValueError('Invalid phone number')

        # canonicalize to E.164
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

class PhonePasswordLoginRequest(BaseModel):
    phone: str
    password: str

    @validator('phone')
    def validate_phone_login(cls, v):
        if not re.match(r'^\+\d{10,15}$', v):
            raise PydanticCustomError('phone.format', 'Phone must be in E.164 format')
        return v

# Helper: send OTP via WhatsApp
def send_whatsapp_otp(phone: str, otp: str) -> JSON:
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

# --- Signup ---
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter((User.phone == payload.phone) | (User.email == payload.email)).first()
    if existing and existing.is_verified:
        raise HTTPException(status_code=400, detail="User already registered and verified.")

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


# --- Verify Signup OTP ---
@router.post("/verify-signup-otp")
def verify_signup_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if user.is_verified:
        return {"status": "already_verified"}
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    user.attempts = 0
    db.commit()
    return {"status": "verified"}

# Login via Email/Password
@router.post("/login/email")
def login_email(payload: EmailLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Account not verified.")
    # TODO: generate JWT/session
    return {"status": "login_successful"}

# --- Request Login OTP ---
@router.post("/login/request-otp")
def request_login_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="Phone number not registered.")
    otp = str(random.randint(1000, 9999))
    expiry = datetime.utcnow() + timedelta(minutes=10)
    user.otp_code = otp
    user.otp_expiry = expiry
    user.attempts = 0
    db.commit()
    send_whatsapp_otp(payload.phone, otp)
    return {"status": "otp_sent"}

# --- Verify Login OTP ---
@router.post("/login/verify-otp")
def verify_login_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(status_code=400, detail="OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid OTP.")
    # TODO: generate JWT/session
    return {"status": "login_successful"}

# --- Logout ---
@router.post("/logout")
def logout():
    return {"status": "logged_out"}
