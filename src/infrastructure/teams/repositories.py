from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.schemas.scheme_user import RoleTeam
from src.infrastructure.db.models.db_team import TeamUser


class SqlAlchemyTeamRoleGetter:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_role(self, user_id: int, team_id: int) -> RoleTeam:
        result = await self._session.scalars(
            select(TeamUser.role).where(
                TeamUser.user_id == user_id,
                TeamUser.team_id == team_id,
            )
        )
        role = result.one_or_none()
        if role is None:
            raise LookupError("user_not_in_team")
        return role
