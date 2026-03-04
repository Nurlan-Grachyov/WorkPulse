from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_active_user, current_superuser
from src.application.schemas.scheme_user import UserRead, UserUpdate
from src.application.services.service_users import UserService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.users.repositories import SqlAlchemyUserRepository

user_router = APIRouter(tags=["users"], prefix="/users")


async def get_user_service(db: AsyncSession = Depends(get_async_session)):
    user_repo = SqlAlchemyUserRepository(db)
    return UserService(user_repo)


@user_router.get(
    "/all_users/",
    response_model=list[UserRead],
    status_code=200,
    summary="Get users",
    description="Get users. Everybody access.",
)
async def get_users(
    current_active_user: User = Depends(current_active_user),
    user_service=Depends(get_user_service),
) -> list[UserRead]:
    try:
        users = await user_service.get_users()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return users


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
    user_service=Depends(get_user_service),
) -> UserRead:
    user = await user_service.get_user(slug)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


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
    user_service=Depends(get_user_service),
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
    try:
        data_for_update_user = data_for_update_user.model_dump(exclude_unset=True)
        user = await user_service.update_user(user_email, data_for_update_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@user_router.delete(
    "/{user_email}/",
    status_code=204,
    summary="Delete user by slug",
    description="Superadmin deletes any user (except superadmins).",
)
async def delete_user(
    slug: str,
    superuser: User = Depends(current_superuser),
    user_service=Depends(get_user_service),
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
    try:
        await user_service.delete_user(slug)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
