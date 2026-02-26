from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import current_active_user
from app.database import get_async_session
from app.models.db_comment import Comment
from app.models.db_task import Task
from app.models.db_user import User
from app.schemas.scheme_comment import CommentCreate, CommentGet, CommentUpdate

comment_router = APIRouter(prefix="/comments", tags=["comments"])


@comment_router.post(
    "/create_comment",
    response_model=CommentGet,
    status_code=201,
    summary="Create new comment",
    description="Creates a new comment for a specific task. "
    "Authenticated users can only create comments for tasks they have access to.",
)
async def create_comment(
    comment: CommentCreate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CommentGet:
    """
    Create a new comment instance with current user as author
    """
    result = await db.scalars(select(Task).where(Task.id == comment.task_id))
    task = result.one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    comment = Comment(**comment.model_dump(), user_id=current_user.id)

    db.add(comment)
    await db.commit()
    await db.refresh(comment)

    return CommentGet.model_validate(comment)


@comment_router.get(
    "/tasks/{task_id}",
    response_model=list[CommentGet],
    status_code=200,
    summary="Get comments by task ID",
    description="Retrieves all comments for a specific task with eager-loaded author and task relationships.",
)
async def get_comments_by_task(
    task_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[CommentGet]:
    """Get comments for specific task"""
    result = await db.scalars(select(Comment).where(Comment.task_id == task_id))
    comments = result.all()

    if not comments:
        raise HTTPException(status_code=404, detail="Comments not found")

    return [CommentGet.model_validate(comment) for comment in comments]


@comment_router.get(
    "/users/",
    response_model=list[CommentGet],
    status_code=200,
    summary="Get comments by user email",
    description="Retrieves all comments authored by a specific user. "
    "Joins through user relationship for efficient filtering.",
)
async def get_comments_by_user(
    user_email: str,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[CommentGet]:
    """Get comments for user by email"""
    result = await db.scalars(
        select(Comment).join(Comment.user).where(User.email == user_email)
    )
    comments = result.all()

    if not comments:
        raise HTTPException(status_code=404, detail="Comments not found")

    return [CommentGet.model_validate(comment) for comment in comments]


@comment_router.patch(
    "/{comment_id}",
    response_model=CommentGet,
    status_code=200,
    summary="Update comment",
    description="Updates an existing comment. "
    "Only comment authors can modify their own comments. Supports partial updates.",
)
async def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> CommentGet:
    """Update comment"""
    result = await db.scalars(
        select(Comment).where(
            Comment.id == comment_id, Comment.user_id == current_user.id
        )
    )
    db_comment = result.first()

    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    update_data = comment.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_comment, field, value)

    await db.commit()
    await db.refresh(db_comment)

    return CommentGet.model_validate(db_comment)


@comment_router.delete(
    "/{comment_id}",
    response_model=None,
    summary="Delete a comment",
    description="Delete a comment by comment's id. Author's comment access",
    status_code=204,
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """Comment deletion"""
    result = await db.scalars(
        select(Comment).where(
            Comment.id == comment_id,
            Comment.user_id == current_user.id,
        )
    )
    comment = result.first()

    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")

    await db.delete(comment)
    await db.commit()
