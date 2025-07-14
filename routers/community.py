from fastapi import APIRouter, Depends
from pydantic import BaseModel
from datetime import datetime
from typing import List
from routers.auth import get_current_user, User

router = APIRouter()

class Post(BaseModel):
    id: int
    author: dict
    timestamp: datetime
    content: str
    likes: int
    replies_count: int

class Comment(BaseModel):
    id: int
    author: dict
    timestamp: datetime
    content: str

class NewPost(BaseModel):
    content: str

class NewComment(BaseModel):
    content: str

@router.get("/posts", response_model=List[Post])
async def list_posts(page: int = 1, per_page: int = 10):
    return [
        Post(
            id=987,
            author={"id": 15, "name": "Michael R.", "avatar_url": None},
            timestamp=datetime.utcnow(),
            content="Just closed a EUR/USD long…",
            likes=24,
            replies_count=8,
        )
    ]

@router.post("/posts", response_model=Post)
async def new_post(p: NewPost, user: User = Depends(get_current_user)):
    return Post(
        id=999,
        author={"id": user.id, "name": user.name, "avatar_url": user.avatar_url},
        timestamp=datetime.utcnow(),
        content=p.content,
        likes=0,
        replies_count=0,
    )

@router.get("/posts/{post_id}/comments", response_model=List[Comment])
async def list_comments(post_id: int):
    return [
        Comment(
            id=1,
            author={"id": 2, "name": "Alice"},
            timestamp=datetime.utcnow(),
            content="Congrats!",
        )
    ]

@router.post("/posts/{post_id}/comments", response_model=Comment)
async def add_comment(
    post_id: int, c: NewComment, user: User = Depends(get_current_user)
):
    return Comment(
        id=2,
        author={"id": user.id, "name": user.name},
        timestamp=datetime.utcnow(),
        content=c.content,
    )
