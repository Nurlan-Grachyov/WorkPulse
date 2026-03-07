from abc import ABC, abstractmethod

from src.application.schemas.scheme_user import RoleTeam
from src.infrastructure.db.models.db_task import Task
from src.infrastructure.db.models.db_user import User


class EvaluationAccessPolicy(ABC):
    @abstractmethod
    def ensure_can_create(self, current_user: User, task: Task) -> None:
        pass


class RoleBasedEvaluationAccessPolicy(EvaluationAccessPolicy):
    def ensure_can_create(self, current_user: User, task: Task) -> bool:
        if current_user.team_link is None:
            raise PermissionError("no_team")

        if current_user.team_link.role is not RoleTeam.MANAGER:
            raise PermissionError("manager_or_admin_access_only")

        if current_user.team_link.team_id != task.team_id:
            raise PermissionError("You don`t exist at this meeting")

        return True
