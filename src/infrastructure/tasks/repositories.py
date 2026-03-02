from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.db_task import Task as TaskModel, Status as TaskStatusModel
from src.domain.tasks.entities import Task, TaskStatus
from src.domain.tasks.repositories import TaskRepository


def _model_to_entity(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        assignee_id=model.assignee_id,
        title=model.title,
        slug=model.slug,
        description=model.description,
        status=TaskStatus(model.status.value),
        deadline=model.deadline,
        team_id=model.team_id,
    )


def _entity_to_model(entity: Task, model: TaskModel | None = None) -> TaskModel:
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

    async def get_by_slug_for_team(self, slug: str, team_id: int) -> Optional[Task]:
        result = await self._session.scalars(
            select(TaskModel).where(
                TaskModel.slug == slug,
                TaskModel.team_id == team_id,
            )
        )
        model = result.one_or_none()
        return _model_to_entity(model) if model else None

    async def get_all(self) -> Sequence[Task]:
        result = await self._session.scalars(select(TaskModel))
        return [_model_to_entity(m) for m in result.all()]

    async def add(self, task: Task) -> Task:
        model = _entity_to_model(task)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def update(self, task: Task) -> Task:
        # найдём текущую модель, обновим её и сохраним
        result = await self._session.scalars(
            select(TaskModel).where(TaskModel.id == task.id)
        )
        model = result.one()
        model = _entity_to_model(task, model=model)
        await self._session.commit()
        await self._session.refresh(model)
        return _model_to_entity(model)

    async def delete(self, task: Task) -> None:
        result = await self._session.scalars(
            select(TaskModel).where(TaskModel.id == task.id)
        )
        model = result.one()
        await self._session.delete(model)
        await self._session.commit()
