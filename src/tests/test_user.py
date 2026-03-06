import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.routers.router_user import (
    delete_user,
    get_user,
    get_users,
    update_user,
)
from src.application.schemas.scheme_user import RoleCompany, UserUpdate
from src.infrastructure.db.models.db_user import User


@pytest.mark.asyncio
async def test_get_users(team_manager_user, db_session: AsyncSession):
    got_users = await get_users(team_manager_user, db_session)
    emails = [user.email for user in got_users]
    assert team_manager_user.email in emails


@pytest.mark.asyncio
async def test_get_user_by_slug(team_manager_user, db_session: AsyncSession):
    user = await get_user(team_manager_user.slug, team_manager_user, db_session)
    assert "user" == user.slug


@pytest.mark.asyncio
async def test_update_user(db_session, admin_user, team_manager_user):
    updated_user = await update_user(
        team_manager_user.email,
        UserUpdate(role=RoleCompany.MANAGER),
        admin_user,
        db_session,
    )
    assert updated_user.email == "user@example.com"
    assert updated_user.role == RoleCompany.MANAGER


@pytest.mark.asyncio
async def test_delete_user(
    db_session: AsyncSession, admin_user: User, team_manager_user: User
):
    await delete_user(
        user_email=team_manager_user.email,
        superuser=admin_user,
        db=db_session,
    )

    result = await db_session.scalars(
        select(User).where(User.email == team_manager_user.email)
    )
    assert result.one_or_none() is None
