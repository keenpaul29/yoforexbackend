# models.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from utils.db import Base

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer,  primary_key=True, index=True)
    name          = Column(String,   nullable=False)
    phone         = Column(String,   unique=True, index=True, nullable=False)
    password_hash = Column(String,   nullable=False)
    is_verified   = Column(Boolean,  default=False, nullable=False)
    otp_code      = Column(String,   nullable=True)
    otp_expiry    = Column(DateTime, nullable=True)
    attempts      = Column(Integer,  default=0, nullable=False)
