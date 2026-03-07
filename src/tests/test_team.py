import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas.scheme_team import TeamCreate
from src.application.schemas.scheme_user import RoleTeam
from src.application.services.service_teams import TeamService
from src.infrastructure.db.models.db_team import Team
from src.infrastructure.db.models.db_user import User
from src.infrastructure.teams.repositories import SqlAlchemyTeamRepository


@pytest.mark.asyncio
async def test_create_team_unit(db_session: AsyncSession, admin_user: User):
    team_repo = SqlAlchemyTeamRepository(db_session)
    team_service = TeamService(team_repo)

    team_in = TeamCreate(title_team="second team")

    # вызываем напрямую, без client
    result = await team_service.create_team(
        team_in=team_in,
    )
    assert result.title == "second team"

    with pytest.raises(ValueError) as exc_info:
        await team_service.create_team(
            team_in=team_in,
        )
    assert "team_exists" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_users_of_team(create_team_with_users, admin_user, db_session):
    team_repo = SqlAlchemyTeamRepository(db_session)
    team_service = TeamService(team_repo)
    users = await team_service.get_users_of_team("team_with_users")
    assert len(users) == 2


@pytest.mark.asyncio
async def test_change_role_user(
    create_team_with_users, admin_user, team_manager_user, db_session
):
    team_repo = SqlAlchemyTeamRepository(db_session)
    team_service = TeamService(team_repo)
    edited_role = await team_service.change_role_user(
        create_team_with_users.slug,
        team_manager_user,
        RoleTeam.USER,
    )
    assert edited_role.role == "user"


@pytest.mark.asyncio
async def test_delete_team(create_team_without_users, admin_user, db_session):
    team_repo = SqlAlchemyTeamRepository(db_session)
    team_service = TeamService(team_repo)
    await team_service.delete_team(create_team_without_users.slug)

    result_team = await db_session.scalars(
        select(Team).where(Team.slug == create_team_without_users.slug)
    )
    assert result_team.one_or_none() is None
