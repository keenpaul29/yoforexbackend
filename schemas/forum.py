from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime

class ForumCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: str = Field(default="#3498db", pattern=r"^#[0-9A-Fa-f]{6}$")

class ForumCategoryCreate(ForumCategoryBase):
    pass

class ForumCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None

class ForumCategory(ForumCategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    post_count: int = 0
    
    class Config:
        orm_mode = True

class ForumPostBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category_id: int

class ForumPostCreate(ForumPostBase):
    pass

class ForumPostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    category_id: Optional[int] = None

class ForumCommentBase(BaseModel):
    content: str = Field(..., min_length=1)
    parent_id: Optional[int] = None

class ForumCommentCreate(ForumCommentBase):
    pass

class ForumCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)

class ForumComment(ForumCommentBase):
    id: int
    author_id: int
    post_id: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    author_username: str = ""
    replies: List['ForumComment'] = []
    
    class Config:
        orm_mode = True

class ForumPost(ForumPostBase):
    id: int
    author_id: int
    is_pinned: bool
    is_locked: bool
    is_deleted: bool
    view_count: int
    created_at: datetime
    updated_at: datetime
    like_count: int = 0
    comment_count: int = 0
    author_username: str = ""
    category_name: str = ""
    latest_comments: List[ForumComment] = []
    
    class Config:
        orm_mode = True

class ForumPostList(BaseModel):
    posts: List[ForumPost]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool

class ForumStats(BaseModel):
    total_posts: int
    total_comments: int
    total_users: int
    recent_posts: List[ForumPost]

# Update ForumComment to handle self-referencing
ForumComment.model_rebuild()
