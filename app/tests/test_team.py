import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_team import Team
from app.models.db_user import User
from app.routers.team import (
    add_user_to_team,
    change_role_user,
    create_team,
    delete_team,
    get_users_of_team,
)
from app.schemas.scheme_team import TeamCreate
from app.schemas.scheme_user import RoleTeam
from app.tests.conftest import db_session


@pytest.mark.asyncio
async def test_create_team_unit(db_session: AsyncSession, admin_user: User):
    team_in = TeamCreate(title_team="second team")

    # вызываем напрямую, без client
    result = await create_team(
        team_in=team_in,
        superuser=admin_user,
        db=db_session,
    )
    assert result.title == "second team"

    with pytest.raises(HTTPException) as exc_info:
        await create_team(
            team_in=team_in,
            superuser=admin_user,
            db=db_session,
        )

    err = exc_info.value
    assert err.status_code == 409
    assert "already exists" in err.detail


@pytest.mark.asyncio
async def test_get_users_of_team(create_team_with_users, admin_user, db_session):
    users = await get_users_of_team("team_with_users", admin_user, db_session)
    assert len(users) == 1


@pytest.mark.asyncio
async def test_add_user_to_team(
    create_team_without_users, team_manager_user, admin_user, db_session
):
    added_user = await add_user_to_team(
        create_team_without_users.slug,
        team_manager_user.email,
        RoleTeam.MANAGER,
        admin_user,
        db_session,
    )
    assert added_user == {
        "message": "User added to team",
        "team_user": {
            "title_team": create_team_without_users.title,
            "user_email": team_manager_user.email,
            "role": RoleTeam.MANAGER,
        },
    }


@pytest.mark.asyncio
async def test_change_role_user(
    create_team_with_users, admin_user, team_manager_user, db_session
):
    edited_role = await change_role_user(
        create_team_with_users.slug,
        team_manager_user.slug,
        RoleTeam.USER,
        db_session,
        admin_user,
    )
    assert edited_role == {
        "message": "Role updated successfully!",
        "user_slug": team_manager_user.slug,
        "team_slug": create_team_with_users.slug,
        "new_role": RoleTeam.USER,
    }


@pytest.mark.asyncio
async def test_delete_team(create_team_without_users, admin_user, db_session):
    await delete_team(create_team_without_users.slug, admin_user, db_session)

    result_team = await db_session.scalars(
        select(Team).where(Team.slug == create_team_without_users.slug)
    )
    assert result_team.one_or_none() is None
