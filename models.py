from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, func
from utils.db import Base
import json
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.types import TypeDecorator, TEXT
from utils.db import Base

class User(Base):
    __tablename__ = "users"

    id            = Column(Integer, primary_key=True, index=True)
    name          = Column(String,  nullable=False)
    email         = Column(String,  unique=True, index=True, nullable=False)
    phone         = Column(String,  unique=True, index=True, nullable=False)
    password_hash = Column(String,  nullable=False)
    is_verified   = Column(Boolean, default=False, nullable=False)
    otp_code      = Column(String,  nullable=True)
    otp_expiry    = Column(DateTime, nullable=True)
    attempts      = Column(Integer, default=0, nullable=False)

class JSONEncodedDict(TypeDecorator):
    """Enables JSN storage by encoding to/from TEXT on SQLite."""
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return json.loads(value)

class SwingAnalysisHistory(Base):
    __tablename__ = "swing_analysis_history"

    id         = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    analysis   = Column(JSONEncodedDict, nullable=False)