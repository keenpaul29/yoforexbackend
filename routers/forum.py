from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_limiter import FastAPILimiter
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, asc, func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi_limiter.depends import RateLimiter
from utils.db import get_db
from utils.security import get_current_user
from models import User, ForumPost, ForumComment, ForumCategory, post_likes, comment_likes
from schemas.forum import (
    ForumPostCreate, ForumPostUpdate, ForumPost, ForumPostList,
    ForumCommentCreate, ForumCommentUpdate, ForumComment,
    ForumCategoryCreate, ForumCategoryUpdate, ForumCategory,
    ForumStats
)

router = APIRouter(prefix="/forum", tags=["forum"])

# Category endpoints
@router.get("/categories", response_model=List[ForumCategory])
async def get_categories(
    db: Session = Depends(get_db),
    include_inactive: bool = False
):
    """Get all forum categories with post counts."""
    query = db.query(ForumCategory)
    if not include_inactive:
        query = query.filter(ForumCategory.is_active == True)
    
    categories = query.order_by(ForumCategory.name).all()
    
    # Add post count for each category
    for category in categories:
        category.post_count = db.query(ForumPost).filter(
            ForumPost.category_id == category.id,
            ForumPost.is_deleted == False
        ).count()
    
    return categories

@router.post("/categories", response_model=ForumCategory)
async def create_category(
    category: ForumCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new forum category (admin only)."""
    # Add admin check here if needed
    
    # Check if category name already exists
    existing = db.query(ForumCategory).filter(ForumCategory.name == category.name).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
        )
    
    db_category = ForumCategory(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    
    return db_category

# Post endpoints
@router.get("/posts", response_model=ForumPostList)
async def get_posts(
    db: Session = Depends(get_db),
    category_id: Optional[int] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in title and content"),
    sort_by: str = Query("created_at", description="Sort by: created_at, updated_at, likes, comments"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    pinned_first: bool = Query(True, description="Show pinned posts first")
):
    """Get paginated forum posts with filtering and sorting."""
    
    # Base query
    query = db.query(ForumPost).filter(ForumPost.is_deleted == False)
    
    # Apply filters
    if category_id:
        query = query.filter(ForumPost.category_id == category_id)
    
    if search:
        search_filter = or_(
            ForumPost.title.ilike(f"%{search}%"),
            ForumPost.content.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
    
    # Count total before pagination
    total = query.count()
    
    # Apply sorting
    if sort_by == "created_at":
        order_col = ForumPost.created_at
    elif sort_by == "updated_at":
        order_col = ForumPost.updated_at
    elif sort_by == "likes":
        # Join with likes table for sorting
        query = query.outerjoin(post_likes).group_by(ForumPost.id)
        order_col = func.count(post_likes.c.user_id)
    elif sort_by == "comments":
        query = query.outerjoin(ForumComment).group_by(ForumPost.id)
        order_col = func.count(ForumComment.id)
    else:
        order_col = ForumPost.created_at
    
    if sort_order == "desc":
        order_col = desc(order_col)
    else:
        order_col = asc(order_col)
    
    # Handle pinned posts
    if pinned_first:
        query = query.order_by(desc(ForumPost.is_pinned), order_col)
    else:
        query = query.order_by(order_col)
    
    # Apply pagination
    offset = (page - 1) * per_page
    posts = query.offset(offset).limit(per_page).options(
        joinedload(ForumPost.author),
        joinedload(ForumPost.category),
        joinedload(ForumPost.comments).joinedload(ForumComment.author)
    ).all()
    
    # Enrich posts with additional data
    enriched_posts = []
    for post in posts:
        post_dict = {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "category_id": post.category_id,
            "author_id": post.author_id,
            "is_pinned": post.is_pinned,
            "is_locked": post.is_locked,
            "is_deleted": post.is_deleted,
            "view_count": post.view_count,
            "created_at": post.created_at,
            "updated_at": post.updated_at,
            "like_count": post.like_count,
            "comment_count": post.comment_count,
            "author_username": post.author.username if post.author else "Unknown",
            "category_name": post.category.name if post.category else "Unknown",
            "latest_comments": [
                {
                    "id": comment.id,
                    "content": comment.content[:100] + "..." if len(comment.content) > 100 else comment.content,
                    "author_username": comment.author.username if comment.author else "Unknown",
                    "created_at": comment.created_at,
                    "author_id": comment.author_id,
                    "post_id": comment.post_id,
                    "parent_id": comment.parent_id,
                    "is_deleted": comment.is_deleted,
                    "updated_at": comment.updated_at,
                    "like_count": comment.like_count,
                    "replies": []
                }
                for comment in sorted(post.comments, key=lambda x: x.created_at, reverse=True)[:3]
                if not comment.is_deleted
            ]
        }
        enriched_posts.append(ForumPost(**post_dict))
    
    return ForumPostList(
        posts=enriched_posts,
        total=total,
        page=page,
        per_page=per_page,
        has_next=page * per_page < total,
        has_prev=page > 1
    )

@router.post("/posts", response_model=ForumPost, dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def create_post(
    post: ForumPostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new forum post."""
    
    # Verify category exists
    category = db.query(ForumCategory).filter(
        ForumCategory.id == post.category_id,
        ForumCategory.is_active == True
    ).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    db_post = ForumPost(**post.dict(), author_id=current_user.id)
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    
    # Load relationships for response
    db_post = db.query(ForumPost).options(
        joinedload(ForumPost.author),
        joinedload(ForumPost.category)
    ).filter(ForumPost.id == db_post.id).first()
    
    return ForumPost(
        **db_post.__dict__,
        author_username=db_post.author.username,
        category_name=db_post.category.name,
        like_count=0,
        comment_count=0,
        latest_comments=[]
    )

@router.get("/posts/{post_id}", response_model=ForumPost)
async def get_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Get a specific forum post with comments."""
    
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id,
        ForumPost.is_deleted == False
    ).options(
        joinedload(ForumPost.author),
        joinedload(ForumPost.category),
        joinedload(ForumPost.comments).joinedload(ForumComment.author)
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Increment view count
    post.view_count += 1
    db.commit()
    
    # Get comments with proper nesting
    comments = db.query(ForumComment).filter(
        ForumComment.post_id == post_id,
        ForumComment.is_deleted == False
    ).options(joinedload(ForumComment.author)).all()
    
    # Organize comments into nested structure
    comment_dict = {}
    root_comments = []
    
    for comment in comments:
        comment_data = {
            "id": comment.id,
            "content": comment.content,
            "author_id": comment.author_id,
            "post_id": comment.post_id,
            "parent_id": comment.parent_id,
            "is_deleted": comment.is_deleted,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at,
            "like_count": comment.like_count,
            "author_username": comment.author.username if comment.author else "Unknown",
            "replies": []
        }
        
        comment_dict[comment.id] = comment_data
        
        if comment.parent_id is None:
            root_comments.append(comment_data)
        else:
            if comment.parent_id in comment_dict:
                comment_dict[comment.parent_id]["replies"].append(comment_data)
    
    return ForumPost(
        **post.__dict__,
        author_username=post.author.username,
        category_name=post.category.name,
        like_count=post.like_count,
        comment_count=len(comments),
        latest_comments=[ForumComment(**comment) for comment in root_comments[:10]]
    )

@router.put("/posts/{post_id}", response_model=ForumPost)
async def update_post(
    post_id: int,
    post_update: ForumPostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a forum post (author only)."""
    
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id,
        ForumPost.is_deleted == False
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this post")
    
    if post.is_locked:
        raise HTTPException(status_code=400, detail="Post is locked and cannot be edited")
    
    # Update fields
    update_data = post_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(post, field, value)
    
    post.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(post)
    
    return await get_post(post_id, db, current_user)

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a forum post (author only)."""
    
    post = db.query(ForumPost).filter(ForumPost.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this post")
    
    post.is_deleted = True
    db.commit()
    
    return {"message": "Post deleted successfully"}

# Comment endpoints
@router.post("/posts/{post_id}/comments", response_model=ForumComment)
async def create_comment(
    post_id: int,
    comment: ForumCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new comment on a post."""
    
    # Verify post exists and is not locked
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id,
        ForumPost.is_deleted == False
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if post.is_locked:
        raise HTTPException(status_code=400, detail="Post is locked for commenting")
    
    # Verify parent comment exists if specified
    if comment.parent_id:
        parent = db.query(ForumComment).filter(
            ForumComment.id == comment.parent_id,
            ForumComment.post_id == post_id,
            ForumComment.is_deleted == False
        ).first()
        if not parent:
            raise HTTPException(status_code=404, detail="Parent comment not found")
    
    db_comment = ForumComment(
        **comment.dict(),
        author_id=current_user.id,
        post_id=post_id
    )
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    
    return ForumComment(
        **db_comment.__dict__,
        author_username=current_user.username,
        like_count=0,
        replies=[]
    )

@router.put("/comments/{comment_id}", response_model=ForumComment)
async def update_comment(
    comment_id: int,
    comment_update: ForumCommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a comment (author only)."""
    
    comment = db.query(ForumComment).filter(
        ForumComment.id == comment_id,
        ForumComment.is_deleted == False
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this comment")
    
    # Check if post is locked
    post = db.query(ForumPost).filter(ForumPost.id == comment.post_id).first()
    if post and post.is_locked:
        raise HTTPException(status_code=400, detail="Cannot edit comment on locked post")
    
    # Update fields
    update_data = comment_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(comment, field, value)
    
    comment.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(comment)
    
    return ForumComment(
        **comment.__dict__,
        author_username=current_user.username,
        like_count=comment.like_count,
        replies=[]
    )

@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (author only)."""
    
    comment = db.query(ForumComment).filter(ForumComment.id == comment_id).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this comment")
    
    comment.is_deleted = True
    db.commit()
    
    return {"message": "Comment deleted successfully"}

# Like/Unlike endpoints
@router.post("/posts/{post_id}/like")
async def toggle_post_like(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a post."""
    
    post = db.query(ForumPost).filter(
        ForumPost.id == post_id,
        ForumPost.is_deleted == False
    ).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check if user already liked the post
    existing_like = db.query(post_likes).filter(
        post_likes.c.user_id == current_user.id,
        post_likes.c.post_id == post_id
    ).first()
    
    if existing_like:
        # Unlike
        db.execute(
            post_likes.delete().where(
                and_(
                    post_likes.c.user_id == current_user.id,
                    post_likes.c.post_id == post_id
                )
            )
        )
        liked = False
    else:
        # Like
        db.execute(
            post_likes.insert().values(
                user_id=current_user.id,
                post_id=post_id
            )
        )
        liked = True
    
    db.commit()
    
    # Get updated like count
    like_count = db.query(post_likes).filter(post_likes.c.post_id == post_id).count()
    
    return {"liked": liked, "like_count": like_count}

@router.post("/comments/{comment_id}/like")
async def toggle_comment_like(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Toggle like on a comment."""
    
    comment = db.query(ForumComment).filter(
        ForumComment.id == comment_id,
        ForumComment.is_deleted == False
    ).first()
    
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check if user already liked the comment
    existing_like = db.query(comment_likes).filter(
        comment_likes.c.user_id == current_user.id,
        comment_likes.c.comment_id == comment_id
    ).first()
    
    if existing_like:
        # Unlike
        db.execute(
            comment_likes.delete().where(
                and_(
                    comment_likes.c.user_id == current_user.id,
                    comment_likes.c.comment_id == comment_id
                )
            )
        )
        liked = False
    else:
        # Like
        db.execute(
            comment_likes.insert().values(
                user_id=current_user.id,
                comment_id=comment_id
            )
        )
        liked = True
    
    db.commit()
    
    # Get updated like count
    like_count = db.query(comment_likes).filter(comment_likes.c.comment_id == comment_id).count()
    
    return {"liked": liked, "like_count": like_count}

# Forum statistics
@router.get("/stats", response_model=ForumStats)
async def get_forum_stats(db: Session = Depends(get_db)):
    """Get forum statistics."""
    
    total_posts = db.query(ForumPost).filter(ForumPost.is_deleted == False).count()
    total_comments = db.query(ForumComment).filter(ForumComment.is_deleted == False).count()
    total_users = db.query(User).count()
    
    # Get recent posts
    recent_posts = db.query(ForumPost).filter(
        ForumPost.is_deleted == False
    ).options(
        joinedload(ForumPost.author),
        joinedload(ForumPost.category)
    ).order_by(desc(ForumPost.created_at)).limit(5).all()
    
    recent_posts_data = []
    for post in recent_posts:
        recent_posts_data.append(ForumPost(
            **post.__dict__,
            author_username=post.author.username,
            category_name=post.category.name,
            like_count=post.like_count,
            comment_count=post.comment_count,
            latest_comments=[]
        ))
    
    return ForumStats(
        total_posts=total_posts,
        total_comments=total_comments,
        total_users=total_users,
        recent_posts=recent_posts_data
    )
