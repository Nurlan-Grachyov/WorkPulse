from abc import ABC, abstractmethod

from src.application.schemas.scheme_user import RoleTeam
from src.infrastructure.db.models.db_user import User


class TaskCreationPolicy(ABC):
    @abstractmethod
    def ensure_can_create(self, user: User) -> None:
        ...


class ManagerOnlyTaskCreationPolicy(TaskCreationPolicy):
    def ensure_can_create(self, user: User) -> None:
        if user.team_link is None:
            raise PermissionError("no_team")

        if user.team_link.role is not RoleTeam.MANAGER:
            raise PermissionError("manager_access_only")
