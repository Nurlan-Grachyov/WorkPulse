from typing import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.application.schemas.scheme_team import TeamCreate
from src.application.schemas.scheme_user import RoleTeam
from src.domain.teams.repositories import TeamRepository
from src.infrastructure.db.models.db_team import Team, TeamUser
from src.infrastructure.db.models.db_user import User


class SqlAlchemyTeamRepository(TeamRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_team(self, team_in: TeamCreate) -> Team:
        created_team = Team(title=team_in.title_team)
        return created_team

    async def get_team_by_title_or_slug(
        self, title: str = None, slug: str = None
    ) -> Team | None:
        stmt = None
        if title is not None:
            stmt = select(Team).where(Team.title == title)
        elif slug is not None:
            stmt = select(Team).where(Team.slug == slug)
        else:
            return None

        result = await self._session.scalars(stmt)
        return result.one_or_none()

    async def get_users_of_team(self, slug_team: str) -> Sequence[User]:
        stmt = (
            select(User)
            .options(selectinload(User.team_link))
            .join(User.team_link)
            .join(TeamUser.team)
            .where(Team.slug == slug_team)
        )

        users = (await self._session.scalars(stmt)).all()
        return users

    async def check_user_in_team(self, user_id: UUID) -> TeamUser | None:
        result_existing_link = await self._session.scalars(
            select(TeamUser).where(TeamUser.user_id == user_id)
        )
        existing_link = result_existing_link.one_or_none()
        if existing_link:
            return existing_link
        else:
            return None

    async def add_user_to_team(
        self, team_id: int, user_id: UUID, role: RoleTeam
    ) -> TeamUser:
        new_team_user = TeamUser(
            team_id=team_id, user_id=user_id, role=role  # USER or MANAGER
        )
        return new_team_user

    async def demote_other_managers(
        self, team_id: int, user_id: UUID, role_data: RoleTeam
    ):
        await self._session.execute(
            update(TeamUser)
            .where(
                TeamUser.team_id == team_id,
                TeamUser.role == role_data,
                TeamUser.user_id != user_id,
            )
            .values(role=RoleTeam.USER)
        )

    async def save(self, obj) -> None:
        try:
            self._session.add(obj)
            await self._session.commit()
            await self._session.refresh(obj)
        except IntegrityError as exc:
            await self._session.rollback()
            # сущность уже есть, нарушен unique, FK, и т.п.
            raise ValueError("integrity_error") from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            # любая другая ошибка работы с БД
            raise RuntimeError("db_error") from exc

    async def delete(self, team: Team) -> None:
        try:
            await self._session.delete(team)
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError("team_has_dependencies") from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            print(exc)
            raise RuntimeError("database_error") from exc
