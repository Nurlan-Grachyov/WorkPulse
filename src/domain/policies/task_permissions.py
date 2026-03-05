from abc import ABC, abstractmethod

from src.application.schemas.scheme_user import RoleCompany, RoleTeam
from src.infrastructure.db.models.db_user import User


class TaskAccessPolicy(ABC):
    @abstractmethod
    def ensure_can_create(self, user: User) -> None: ...


class RoleBasedTaskAccessPolicy(TaskAccessPolicy):
    def ensure_can_create(self, user: User) -> None:
        if user.team_link is None:
            raise PermissionError("no_team")

        if user.team_link.role is not RoleTeam.MANAGER:
            raise PermissionError("manager_access_only")

    def ensure_get_all_tasks(self, user: User):
        if user.role is RoleCompany.ADMIN:
            return True
        return False
