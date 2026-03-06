from abc import ABC, abstractmethod

from src.application.schemas.scheme_user import RoleCompany, RoleTeam
from src.infrastructure.db.models.db_user import User


class MeetingAccessPolicy(ABC):
    @abstractmethod
    def ensure_can_create(self, user: User) -> None:
        pass


class RoleBasedMeetingAccessPolicy(MeetingAccessPolicy):
    def ensure_can_create(self, user: User) -> None:
        if user.team_link is None:
            raise PermissionError("no_team")

        if user.team_link.role is not (RoleTeam.MANAGER or RoleCompany.ADMIN):
            raise PermissionError("manager_or_admin_access_only")

    def ensure_can_update_delete(self, current_user: User, db_meeting) -> bool:
        if current_user.team_link is None:
            raise PermissionError("no_team")

        if current_user.team_link.role is not (RoleTeam.MANAGER or RoleCompany.ADMIN):
            raise PermissionError("manager_or_admin_access_only")

        if any(user.id == current_user.id for user in db_meeting.users):
            raise PermissionError("You don`t exist at this meeting")

        return True

    def can_get_all_meetings(self, current_user):
        return current_user.role is RoleCompany.ADMIN
