# routers/auth.py
import logging
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any
import random
import os
import requests
from passlib.context import CryptContext
from dotenv import load_dotenv

from utils.db import get_db
from models import User

# Setup
logger = logging.getLogger(__name__)
load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
router = APIRouter(prefix="/auth", tags=["auth"])

# WATI Configuration
WATI_API_ENDPOINT = os.getenv("WATI_API_ENDPOINT")  # e.g. https://live-mt-server.wati.io/436184
WATI_ACCESS_TOKEN = os.getenv("WATI_ACCESS_TOKEN")  # e.g. Bearer <token>

# Schemas
JSON = Dict[str, Any]
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    phone: str
    password: str

class OTPRequest(BaseModel):
    phone: str

class OTPVerifyRequest(BaseModel):
    phone: str
    otp: str

class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str

class PhonePasswordLoginRequest(BaseModel):
    phone: str
    password: str

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
        raise HTTPException(400, "User already registered and verified.")

    otp = f"{random.randint(1000,9999)}"
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
        raise HTTPException(404, "User not found.")
    if user.is_verified:
        return {"status": "already_verified"}
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(400, "OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(400, "Invalid OTP.")
    user.is_verified = True
    user.otp_code = None
    user.otp_expiry = None
    user.attempts = 0
    db.commit()
    return {"status": "verified"}

# --- Login via Email/Password ---
@router.post("/login/email")
def login_email(payload: EmailLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not pwd_context.verify(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password.")
    if not user.is_verified:
        raise HTTPException(403, "Account not verified.")
    # TODO: generate JWT/session
    return {"status": "login_successful"}

# --- Request Login OTP ---
@router.post("/login/request-otp")
def request_login_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.phone == payload.phone).first()
    if not user:
        raise HTTPException(404, "Phone number not registered.")
    otp = f"{random.randint(1000,9999)}"
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
        raise HTTPException(404, "User not found.")
    if datetime.utcnow() > user.otp_expiry:
        raise HTTPException(400, "OTP expired.")
    if payload.otp != user.otp_code:
        user.attempts += 1
        db.commit()
        raise HTTPException(400, "Invalid OTP.")
    # TODO: generate JWT/session
    return {"status": "login_successful"}

# --- Logout ---
@router.post("/logout")
def logout():
    # client should drop token; implement blacklisting if needed
    return {"status": "logged_out"}
