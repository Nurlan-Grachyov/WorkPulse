from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.tasks.repositories import TaskRepository
from src.infrastructure.db.models.db_task import Task
from src.infrastructure.db.models.db_team import TeamUser
from src.infrastructure.db.models.db_user import User


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_task_by_slug_for_team(self, slug: str) -> Optional[Task]:
        result_task = await self._session.scalars(select(Task).where(Task.slug == slug))
        task = result_task.one_or_none()
        if task is None:
            raise LookupError("task_not_found")
        return task

    async def get_task_by_id(self, task_id: int) -> Task:
        result_task = await self._session.scalars(
            select(Task).where(Task.id == task_id)
        )
        task = result_task.one_or_none()
        if task is None:
            raise LookupError("task_not_found")
        return task

    async def get_all_task_for_admin(self) -> Sequence[Task]:
        result_task = await self._session.scalars(select(Task))
        tasks = result_task.all()
        return tasks

    async def get_all_task_for_user(self, user_id) -> Sequence[Task]:
        result_user = await self._session.scalars(
            select(User).options(joinedload(User.team_link)).where(User.id == user_id)
        )
        user = result_user.one_or_none()

        if user.team_link:
            result_task = await self._session.scalars(
                select(Task).where(Task.team_id == user.team_link.team_id)
            )
            tasks = result_task.all()
        else:
            return []
        return tasks

    async def add_task(
        self, task: dict, user_id: UUID
    ) -> tuple[User | None, User | None, Task | None]:
        # 1. Автор с командой
        author_result = await self._session.scalars(
            select(User).options(joinedload(User.team_link)).where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")

        if author.team_link is None:
            raise PermissionError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Исполнитель в той же команде
        assignee_result = await self._session.scalars(
            select(User).where(
                User.id == task.get("assignee_id"),
                User.is_active,
                User.team_link.has(TeamUser.team_id == team_id),
            )
        )
        assignee = assignee_result.one_or_none()
        if assignee is None:
            raise LookupError("assignee_not_found")

        # 3. Проверка уникальности slug в команде
        task_result = await self._session.scalars(
            select(Task).where(
                Task.slug == task.get("slug"),
                Task.team_id == team_id,
            )
        )
        existing_task = task_result.one_or_none()

        return author, assignee, existing_task

    async def update_task(
        self,
        task_slug: str,
        user_id: UUID,
    ) -> tuple[User, Task]:
        # 1. Автор с командой
        author_result = await self._session.scalars(
            select(User).options(joinedload(User.team_link)).where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")
        if author.team_link is None:
            raise LookupError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Таска этой команды по slug
        task_result = await self._session.scalars(
            select(Task).where(
                Task.slug == task_slug,
                Task.team_id == team_id,
            )
        )
        task_model = task_result.one_or_none()
        if task_model is None:
            raise LookupError("task_not_found")

        return author, task_model

    async def delete_task(self, slug_task: str, user_id: UUID) -> tuple[User, Task]:
        author_result = await self._session.scalars(
            select(User).options(joinedload(User.team_link)).where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")
        if author.team_link is None:
            raise LookupError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Таска этой команды по slug
        task_result = await self._session.scalars(
            select(Task).where(
                Task.slug == slug_task,
                Task.team_id == team_id,
            )
        )
        task_model = task_result.one_or_none()
        if task_model is None:
            raise LookupError("task_not_found")

        return author, task_model

    async def save(self, task) -> None:
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)

    async def delete(self, task_model: Task) -> None:
        await self._session.delete(task_model)
        await self._session.commit()
