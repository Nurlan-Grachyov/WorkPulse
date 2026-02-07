from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_async_session
from app.models.db_team import Team, TeamUser
from app.models.db_user import User
from app.schemas.scheme_team import TeamCreate, TeamGet
from auth import current_superuser

team_router = APIRouter()


@team_router.post("/create_team", response_model=TeamGet, status_code=201)
async def create_team(
    team: TeamCreate,
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    result = await db.execute(select(Team).where(...))
    existing_team = result.scalars().first()
    if existing_team:
        raise HTTPException(
            status_code=409, detail="Команда с таким названием уже существует"
        )

    new_team = Team(**team.model_dump())

    db.add(new_team)
    await db.commit()
    await db.refresh(new_team)

    return new_team


@team_router.get("users_team", status_code=200)
async def get_users_of_team(
    title_team: str,
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    stmt = (
        select(User)
        .join(TeamUser)
        .join(Team)
        .where(Team.title == title_team)
        .options(selectinload(User.tasks), selectinload(User.comments))
    )

    result = await db.execute(stmt)
    return result.scalars().all()


@team_router.post("add_user_to_team", status_code=200)
async def add_user_to_team(
    user_email: str,
    team_title: str,
    superuser: User = Depends(current_superuser),
    db: AsyncSession = Depends(get_async_session),
):
    pass
