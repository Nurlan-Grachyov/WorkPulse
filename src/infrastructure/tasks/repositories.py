from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.tasks.entities import Task
from src.domain.tasks.repositories import TaskRepository
from src.infrastructure.db.models.db_task import Status as TaskStatusModel, Status
from src.infrastructure.db.models.db_task import Task as TaskModel
from src.infrastructure.db.models.db_team import TeamUser
from src.infrastructure.db.models.db_user import User


def task_model_to_entity(model: TaskModel) -> Task:
    return Task(
        assignee_id=model.assignee_id,
        title=model.title,
        slug=model.slug,
        description=model.description,
        status=Status(model.status.value),
        deadline=model.deadline,
        team_id=model.team_id,
    )


def task_entity_to_model(entity: Task, model: TaskModel | None = None) -> TaskModel:
    if model is None:
        model = TaskModel()
    model.assignee_id = entity.assignee_id
    model.title = entity.title
    model.slug = entity.slug
    model.description = entity.description
    model.status = TaskStatusModel(entity.status.value)
    model.deadline = entity.deadline
    model.team_id = entity.team_id
    return model


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_task_by_slug_for_team(self, slug: str) -> Optional[TaskModel]:
        result_task = await self._session.scalars(select(TaskModel).where(TaskModel.slug == slug))
        task = result_task.one_or_none()
        if task is None:
            raise LookupError("user_not_found")
        return task

    async def get_all_task(self) -> Sequence[Task]:
        pass

    async def add_task(self, task: Task, user_id: UUID) -> tuple[User | None, User | None, TaskModel | None]:
        # 1. Автор с командой
        author_result = await self._session.scalars(
            select(User)
            .options(joinedload(User.team_link))
            .where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")

        if author.team_link is None:
            raise LookupError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Исполнитель в той же команде
        assignee_result = await self._session.scalars(
            select(User).where(
                User.id == task.assignee_id,
                User.is_active,
                User.team_link.has(TeamUser.team_id == team_id),
            )
        )
        assignee = assignee_result.one_or_none()
        if assignee is None:
            raise LookupError("assignee_not_found")

        # 3. Проверка уникальности slug в команде
        task_result = await self._session.scalars(
            select(TaskModel).where(
                TaskModel.slug == task.slug,
                TaskModel.team_id == team_id,
            )
        )
        existing_task = task_result.one_or_none()

        return author, assignee, existing_task

    async def update_task(
            self,
            task_slug: str,
            user_id: UUID,
    ) -> tuple[User, TaskModel]:
        # 1. Автор с командой
        author_result = await self._session.scalars(
            select(User)
            .options(joinedload(User.team_link))
            .where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")
        if author.team_link is None:
            raise LookupError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Таска этой команды по slug
        task_result = await self._session.scalars(
            select(TaskModel).where(
                TaskModel.slug == task_slug,
                TaskModel.team_id == team_id,
            )
        )
        task_model = task_result.one_or_none()
        if task_model is None:
            raise LookupError("task_not_found")

        return author, task_model

    async def delete_task(self, task: TaskModel, user_id: UUID) -> tuple[User, TaskModel]:
        author_result = await self._session.scalars(
            select(User)
            .options(joinedload(User.team_link))
            .where(User.id == user_id)
        )
        author = author_result.one_or_none()
        if author is None:
            raise LookupError("author_not_found")
        if author.team_link is None:
            raise LookupError("author_no_team")

        team_id = author.team_link.team_id

        # 2. Таска этой команды по slug
        task_result = await self._session.scalars(
            select(TaskModel).where(
                TaskModel.slug == task.slug,
                TaskModel.team_id == team_id,
            )
        )
        task_model = task_result.one_or_none()
        if task_model is None:
            raise LookupError("task_not_found")

        return author, task_model

    async def save(self, task) -> None:
        result = await self._session.scalars(
            select(TaskModel).where(TaskModel.id == task.id)
        )
        model = result.one_or_none()
        if model is None:
            raise LookupError("user_not_found")
        model = task_entity_to_model(task, model=model)
        await self._session.commit()
        await self._session.refresh(model)
