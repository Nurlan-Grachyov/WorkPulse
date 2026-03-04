from typing import Optional, Sequence

from src.domain.policies.task_creation import TaskCreationPolicy
from src.domain.tasks.repositories import TaskRepository
from src.domain.tasks.services import update_task_fields
from src.infrastructure.db.models.db_task import Status, Task
from src.infrastructure.db.models.db_user import User


class TaskService:
    def __init__(self, tasks: TaskRepository, policy: TaskCreationPolicy):
        self._tasks = tasks
        self._policy = policy

    async def get_task_by_slug_for_team(self, slug: str) -> Optional[Task]:
        task = await self._tasks.get_task_by_slug_for_team(slug)
        if task is None:
            raise LookupError("task_not_found")
        return task

    async def get_all_task(self, current_user) -> Sequence[Task]:
        tasks = await self._tasks.get_all_task(current_user.id)
        return tasks

    async def add_task(self, task: dict, user: User) -> Task:
        author, assignee, existing_task = await self._tasks.add_task(task, user.id)
        self._policy.ensure_can_create(author)
        if existing_task is not None:
            raise ValueError("task_slug_exists")

        # сохраняем
        model = Task(
            assignee_id=task.get("assignee_id"),
            title=task.get("title"),
            slug=task.get("slug"),
            description=task.get("description"),
            status=Status(task.get("status")),
            deadline=task.get("deadline"),
            team_id=author.team_link.team_id,
        )
        await self._tasks.save(model)
        return model

    async def update_task(
        self,
        task_slug: str,
        data_for_update: dict,
        current_user: User,
    ) -> Task:
        # 1. Готовим данные (автор + таска)
        author, task_model = await self._tasks.update_task(task_slug, current_user.id)

        # 2. Проверяем права (можно ли этому автору менять задачи)
        self._policy.ensure_can_create(author)

        # 3. Обновляем поля из dict (title, description, status, deadline, assignee_id...)
        updated_model = update_task_fields(task_model, data_for_update)

        # 4. Сохраняем
        await self._tasks.save(updated_model)
        return updated_model

    async def delete_task(self, slug_task: str, current_user: User) -> None:
        author, task_model = await self._tasks.delete_task(slug_task, current_user.id)

        # 2. Проверяем права (можно ли этому автору менять задачи)
        self._policy.ensure_can_create(author)

        await self._tasks.delete(task_model)
