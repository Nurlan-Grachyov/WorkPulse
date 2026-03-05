from abc import ABC, abstractmethod

from src.application.schemas.scheme_user import RoleTeam


class UniqueTeamRolePolicy(ABC):
    @abstractmethod
    def is_satisfied(self, role_data: str) -> bool:
        """Проверяет, выполняется ли правило уникальности роли в команде."""
        ...


class UniqueRolesPolicy(UniqueTeamRolePolicy):
    def is_unique(self, role_data: str) -> bool:
        return role_data is RoleTeam.MANAGER
