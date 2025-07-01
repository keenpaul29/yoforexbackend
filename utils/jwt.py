# utils/jwt.py
import os
from datetime import datetime, timedelta
from typing import Union

from jose import JWTError, jwt

# Load from env
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 60))

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    """
    Creates a JWT token.
    - data: payload (e.g. {"sub": user.email})
    - expires_delta: timedelta for expiration (defaults to ACCESS_TOKEN_EXPIRE_MINUTES)
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_access_token(token: str) -> dict:
    """
    Verifies the JWT and returns the payload if valid.
    Raises JWTError on failure.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload
