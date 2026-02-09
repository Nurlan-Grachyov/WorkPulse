from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi_users import models
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.database import get_async_session
from app.models.db_team import TeamUser, Team
from app.models.db_user import User
from app.schemas.scheme_user import RoleCompany, UserRead, UserUpdate, UserReadWithTeamLink
from auth import UserManager, current_active_user, current_superuser, get_user_manager

user_router = APIRouter(tags=["users"], prefix="/users")


@user_router.get("/all_users", response_model=list[UserRead], status_code=200,
                 summary="Get users",
                 description="Get users. Everybody access.")
async def get_users(current_active_user: User = Depends(current_active_user),
                    db: AsyncSession = Depends(get_async_session)) -> list[UserRead]:
    users = await db.scalars(
        select(User).where(
            User.is_active
        )
    )

    if not users:
        raise HTTPException(status_code=404, detail="Users not found")

    return [UserRead.model_validate(user) for user in users]


@user_router.get("/{slug}", response_model=UserRead, status_code=200,
                 summary="Get user",
                 description="Get user with team and members info.. Everybody access.")
async def get_user(slug: str, current_active_user: User = Depends(current_active_user),
                   db: AsyncSession = Depends(get_async_session)) -> UserReadWithTeamLink:
    result = await db.scalars(
        select(User)
        .options(
            joinedload(User.team_link),
            joinedload(TeamUser.team).load_only(Team.title),
            selectinload(TeamUser.team).selectinload(Team.members)
        )
        .where(User.slug == slug, User.is_active)
    )

    user = result.one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserReadWithTeamLink.model_validate(user)


@user_router.patch(
    "/{user_slug}/update",
    response_model=UserRead,
    status_code=200,
    summary="Update user role",
    description="Updates global company role for user. Superadmin access only.",
)
async def update_user(
        data_for_update_user: UserUpdate,
        role: RoleCompany = Body(
            ..., embed=True, description="New company role (USER/MANAGER/ADMIN)"
        ),
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
    user = await db.scalar(
        select(User).where(
            User.slug == data_for_update_user.user_slug, User.is_active
        )  # Only active users
    )

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update company role
    user.role = role

    await db.commit()
    await db.refresh(user)

    return UserRead.model_validate(user)


@user_router.delete(
    "/delete_me",
    status_code=204,
    summary="Delete current user",
    description="Self-service user deletion. Current user only.",
)
async def delete_current_user(
        user: models.UP = Depends(current_active_user),
        user_manager: UserManager = Depends(get_user_manager),
) -> None:
    """
    Allows current user to delete their own account.

    **Features:**
    - Uses FastAPI Users user_manager for proper cleanup
    - Deletes user sessions, tokens, etc.
    - Returns 204 No Content (empty response)

    **Permissions:**
    - Current authenticated user only
    """
    await user_manager.delete(user)
    return None  # 204 No Content


@user_router.delete(
    "/{user_slug}/delete",
    status_code=204,
    summary="Delete user by slug",
    description="Superadmin deletes any user (except superadmins).",
)
async def delete_user(
        user_slug: str,
        superuser: User = Depends(current_superuser),
        db: AsyncSession = Depends(get_async_session),
        user_manager: UserManager = Depends(get_user_manager),
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
    # Find active user by slug
    user = await db.scalar(select(User).where(User.slug == user_slug, User.is_active))

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Safety check: prevent superadmin deletion
    if user.role == RoleCompany.ADMIN:
        raise HTTPException(status_code=403, detail="Cannot delete superadmin accounts")

    # Delete user from database
    await db.delete(user)
    await db.commit()
    return None  # 204 No Content
