from typing import Optional, Sequence

from src.domain.policies.task_permissions import RoleBasedTaskAccessPolicy
from src.domain.tasks.repositories import TaskRepository
from src.domain.tasks.services import update_task_fields
from src.infrastructure.db.models.db_task import Status, Task
from src.infrastructure.db.models.db_user import User


class TaskService:
    def __init__(self, tasks: TaskRepository, policy: RoleBasedTaskAccessPolicy):
        self._tasks = tasks
        self._policy = policy

    async def get_task_by_slug_for_team(self, slug: str) -> Optional[Task]:
        task = await self._tasks.get_task_by_slug_for_team(slug)
        if task is None:
            raise LookupError("task_not_found")
        return task

    async def get_all_task(self, current_user) -> Sequence[Task]:
        if self._policy.ensure_get_all_tasks(current_user):
            tasks = await self._tasks.get_all_task_for_admin()
        else:
            tasks = await self._tasks.get_all_task_for_user(current_user.id)
        return tasks

    async def add_task(self, task: dict, user: User) -> Task:
        author, assignee, existing_task = await self._tasks.add_task(task, user.id)
        self._policy.ensure_can_create(author)
        print(repr(existing_task))
        print(type(existing_task))
        if existing_task is None:
            print("EXACTLY NONE")
        if existing_task is not None:
            print("whaaaat")
            raise ValueError("task_slug_exists")

        # сохраняем
        model = Task(
            assignee_id=assignee.id,
            title=task.get("title"),
            description=task.get("description"),
            status=task.get("status") or Status.OPEN,
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
