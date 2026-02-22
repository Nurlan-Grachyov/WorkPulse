import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import fastapi_app
from app.models.db_team import Team
from app.models.db_user import User
from app.routers.team import create_team
from app.schemas.scheme_team import TeamCreate


@pytest.mark.asyncio
async def test_create_team(db_session, client, override_auth_admin):
    result_team = await db_session.scalars(
        select(Team).where(Team.title == "first team")
    )
    db_team = result_team.one_or_none()
    try:
        payload = {"title_team": "first team"}
        if not db_team:
            response = await client.post("/team/create_team", json=payload)
            print(response.json())
            assert response.status_code == 201
            team = response.json()
            assert team.get("title") == "first team"

        response = await client.post("/team/create_team", json=payload)
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_team_unit(db_session: AsyncSession, admin_user: User):
    team_in = TeamCreate(title_team="second team")

    # вызываем напрямую, без client
    result = await create_team(
        team_in=team_in,
        superuser=admin_user,
        db=db_session,
    )
    print(result)
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