from typing import Sequence
from uuid import UUID

from src.application.schemas.scheme_team import TeamCreate
from src.application.schemas.scheme_user import RoleTeam
from src.domain.policies.team_permissions import UniqueRolesPolicy
from src.domain.teams.repositories import TeamRepository
from src.infrastructure.db.models.db_team import Team, TeamUser
from src.infrastructure.db.models.db_user import User


class TeamService:
    def __init__(self, teams: TeamRepository):
        self._teams = teams

    async def get_team_by_title_or_slug(
        self, title: str = None, slug: str = None
    ) -> Team:
        team = await self._teams.get_team_by_title_or_slug(title=title, slug=slug)
        if team is None:
            raise LookupError("team_not_found")
        return team

    async def create_team(self, team_in: TeamCreate) -> Team:
        try:
            await self.get_team_by_title_or_slug(title=team_in.title_team)
            raise ValueError("team_exists")
        except LookupError:
            pass

        created_team = await self._teams.create_team(team_in)

        try:
            await self._teams.save(created_team)
        except ValueError as exc:
            # integrity_error из save — значит, unique в БД сработал
            if "integrity_error" in str(exc):
                raise ValueError("team_exists") from exc
            raise

        return created_team

    async def get_users_of_team(self, slug_team: str) -> Sequence[User] | None:
        team = await self._teams.get_team_by_title_or_slug(slug=slug_team)
        users = await self._teams.get_users_of_team(slug_team)
        return users

    async def check_user_in_team(self, user_id: UUID, team_id: int) -> TeamUser | None:
        return await self._teams.check_user_in_team(user_id, team_id)

    async def add_user_to_team(
        self, slug_team: str, user_id: UUID, role: RoleTeam
    ) -> TeamUser:
        try:
            team = await self.get_team_by_title_or_slug(slug=slug_team)
        except LookupError:
            raise

        existing_link = await self.check_user_in_team(user_id, team.id)
        if existing_link:
            raise ValueError

        added_user = await self._teams.add_user_to_team(team.id, user_id, role)

        await self._teams.save(added_user)

        return added_user

    async def change_role_user(self, slug_team: str, user: User, role_data: RoleTeam):
        try:
            team = await self.get_team_by_title_or_slug(slug=slug_team)
        except LookupError:
            raise

        team_user = await self.check_user_in_team(user.id, team.id)
        if team_user is None:
            raise LookupError("user_not_in_team")

        check_role = UniqueRolesPolicy()
        if check_role.is_unique(role_data):
            await self._teams.demote_other_managers(team.id, user.id, role_data)
        team_user.role = role_data

        await self._teams.save(team_user)

        return team_user

    async def delete_team(self, slug_team: str):
        try:
            team = await self.get_team_by_title_or_slug(slug=slug_team)
        except LookupError as exc:
            raise ValueError(f"team_not_found: {slug_team}") from exc

        try:
            await self._teams.delete(team)
        except ValueError as exc:
            if "team_has_dependencies" in str(exc):
                raise ValueError("cannot_delete_team_with_dependencies")
            raise
        except RuntimeError:
            raise RuntimeError("failed_to_delete_team")
