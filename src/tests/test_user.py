import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas.scheme_user import RoleCompany, UserUpdate
from src.application.services.service_users import UserService
from src.infrastructure.db.models.db_user import User
from src.infrastructure.users.repositories import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_get_users(team_manager_user, db_session: AsyncSession):
    user_repo = SqlAlchemyUserRepository(db_session)
    user_service = UserService(user_repo)

    got_users = await user_service.get_users()

    emails = [user.email for user in got_users]
    assert team_manager_user.email in emails


@pytest.mark.asyncio
async def test_get_user_by_slug(team_manager_user, db_session: AsyncSession):
    user_repo = SqlAlchemyUserRepository(db_session)
    user_service = UserService(user_repo)
    user = await user_service.get_user(email="user@example.com")
    assert "user" == user.slug

    user = await user_service.get_user(slug="user")
    assert "user" == user.slug

@pytest.mark.asyncio
async def test_get_user_with_team_link(team_manager_user, db_session: AsyncSession):
    user_repo = SqlAlchemyUserRepository(db_session)
    user_service = UserService(user_repo)
    user = await user_service.get_user_with_team_link(email="user@example.com")
    assert "user" == user.slug

    user = await user_service.get_user_with_team_link(slug="user")
    assert "user" == user.slug

@pytest.mark.asyncio
async def test_update_user(db_session, admin_user, team_manager_user):
    user_repo = SqlAlchemyUserRepository(db_session)
    user_service = UserService(user_repo)
    data = UserUpdate(role=RoleCompany.MANAGER)
    python_data = data.model_dump(exclude_unset=True)
    updated_user = await user_service.update_user(
        team_manager_user.email,
        python_data,
    )
    assert updated_user.email == "user@example.com"
    assert updated_user.role == RoleCompany.MANAGER


@pytest.mark.asyncio
async def test_delete_user(
    db_session: AsyncSession, admin_user: User, team_manager_user: User
):
    user_repo = SqlAlchemyUserRepository(db_session)
    user_service = UserService(user_repo)
    await user_service.delete_user(
        slug=team_manager_user.slug,
    )

    result = await db_session.scalars(
        select(User).where(User.email == team_manager_user.email)
    )
    assert result.one_or_none() is None
