from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_async_session
from app.models.db_user import User
from app.schemas.scheme_user import RoleCompany, UserRead, UserUpdate
from auth import current_active_user, current_superuser

user_router = APIRouter(tags=["users"], prefix="/users")


@user_router.get(
    "/all_users/",
    response_model=list[UserRead],
    status_code=200,
    summary="Get users",
    description="Get users. Everybody access.",
)
async def get_users(
    current_active_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> list[UserRead]:
    users = await db.scalars(select(User).where(User.is_active))

    return [UserRead.model_validate(user) for user in users]


@user_router.get(
    "/{slug}/",
    response_model=UserRead,
    status_code=200,
    summary="Get user",
    description="Get user with team and members info.. Everybody access.",
)
async def get_user(
    slug: str,
    current_active_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
) -> UserRead:
    result = await db.scalars(select(User).where(User.slug == slug, User.is_active))
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserRead.model_validate(user)


@user_router.patch(
    "/{user_email}/",
    response_model=UserRead,
    status_code=200,
    summary="Update user role",
    description="Updates global company role for user. Superadmin access only.",
)
async def update_user(
    user_email: str,
    data_for_update_user: UserUpdate,
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
) -> UserRead:
    """
    Updates user's global company role (User.role field).

    **Validations:**
    - User exists and is active
    - Superadmin access required
    - Only company-wide role (not team-specific)

    **Returns:**
    - Updated UserRead schema with new role
    """
    # Find active user by slug
    result = await db.scalars(
        select(User).where(
            User.email == user_email, User.is_active
        )  # Only active users
    )
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update company role
    user.role = data_for_update_user.role

    await db.commit()
    await db.refresh(user)

    return UserRead.model_validate(user)


@user_router.delete(
    "/{user_email}/",
    status_code=204,
    summary="Delete user by slug",
    description="Superadmin deletes any user (except superadmins).",
)
async def delete_user(
    user_email: str,
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
) -> None:
    """
    Superadmin deletes user by slug with safety checks.

    **Safety validations:**
    1. User exists and is active
    2. Cannot delete superadmin accounts
    3. Proper database cleanup

    **Returns:**
    - 204 No Content on success
    """
    # Find active user by email
    result = await db.scalars(
        select(User).where(User.email == user_email, User.is_active)
    )
    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Safety check: prevent superadmin deletion
    if user.role == RoleCompany.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete superadmin accounts")

    # Delete user from database
    await db.delete(user)
    await db.commit()
    return None  # 204 No Content
