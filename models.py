from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, func, Text, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

from utils.db import Base
import json
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.types import TypeDecorator, TEXT
from utils.db import Base

# Association table for post likes
post_likes = Table(
    'post_likes',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('post_id', Integer, ForeignKey('forum_posts.id'), primary_key=True)
)

# Association table for comment likes
comment_likes = Table(
    'comment_likes',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('comment_id', Integer, ForeignKey('forum_comments.id'), primary_key=True)
)

class ForumCategory(Base):
    __tablename__ = "forum_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    color = Column(String(7), default="#3498db")  # Hex color code
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    posts = relationship("ForumPost", back_populates="category")

class ForumPost(Base):
    __tablename__ = "forum_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("forum_categories.id"), nullable=False)
    is_pinned = Column(Boolean, default=False)
    is_locked = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="forum_posts")
    category = relationship("ForumCategory", back_populates="posts")
    comments = relationship("ForumComment", back_populates="post", cascade="all, delete-orphan")
    likes = relationship("User", secondary=post_likes, back_populates="liked_posts")
    
    @property
    def like_count(self):
        return len(self.likes)
    
    @property
    def comment_count(self):
        return len([c for c in self.comments if not c.is_deleted])

class ForumComment(Base):
    __tablename__ = "forum_comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    post_id = Column(Integer, ForeignKey("forum_posts.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("forum_comments.id"), nullable=True)  # For nested comments
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    author = relationship("User", back_populates="forum_comments")
    post = relationship("ForumPost", back_populates="comments")
    parent = relationship("ForumComment", remote_side=[id])
    replies = relationship("ForumComment", back_populates="parent")
    likes = relationship("User", secondary=comment_likes, back_populates="liked_comments")
    
    @property
    def like_count(self):
        return len(self.likes)


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
    forum_posts = relationship("ForumPost", back_populates="author")
    forum_comments = relationship("ForumComment", back_populates="author")
    liked_posts = relationship("ForumPost", secondary=post_likes, back_populates="likes")
    liked_comments = relationship("ForumComment", secondary=comment_likes, back_populates="likes")

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