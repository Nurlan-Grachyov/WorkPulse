from typing import Optional, Protocol, Sequence
from uuid import UUID

from ...infrastructure.db.models.db_task import Task
from ...infrastructure.db.models.db_user import User


class TaskRepository(Protocol):
    async def get_task_by_slug_for_team(self, slug: str) -> Optional[Task]: ...

    async def get_all_task(self, user_id: UUID) -> Sequence[Task]: ...

    async def add_task(
        self, task: dict, user_id: UUID
    ) -> tuple[User | None, User | None, Task | None]: ...

    async def update_task(
        self,
        task_slug: str,
        user_id: UUID,
    ) -> tuple[User, Task]: ...

    async def delete_task(self, slug_task: str, user_id: UUID) -> tuple[User, Task]: ...

    async def save(self, task) -> None: ...

    async def delete(self, task_model: Task) -> None: ...
