from typing import Protocol, Sequence
from uuid import UUID

from src.application.schemas.scheme_team import TeamCreate
from src.application.schemas.scheme_user import RoleTeam
from src.infrastructure.db.models.db_team import Team, TeamUser
from src.infrastructure.db.models.db_user import User


class TeamRepository(Protocol):

    async def create_team(self, team_in: TeamCreate) -> Team: ...

    async def get_team_by_title_or_slug(
        self, title: str = None, slug: str = None
    ) -> Team | None: ...

    async def save(self, object) -> None: ...

    async def get_users_of_team(self, slug_team: str) -> Sequence[User]: ...

    async def check_user_in_team(
        self, user_id: UUID
    ) -> TeamUser | None: ...

    async def add_user_to_team(
        self, team_id: int, user_id: UUID, role: RoleTeam
    ) -> TeamUser: ...

    async def demote_other_managers(
        self, team_id: int, user_id: UUID, role_data: RoleTeam
    ): ...

    async def delete(self, team: Team) -> None: ...
