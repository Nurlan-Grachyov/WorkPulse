from typing import Sequence

from src.domain.tasks.entities import Task, TaskStatus
from src.domain.tasks.repositories import TaskRepository
from src.domain.tasks.services import update_task_fields
from src.application.schemas.scheme_task import TaskCreate, TaskUpdate
from src.infrastructure.db.models.db_user import User
from src.application.schemas.scheme_user import RoleCompany, RoleTeam


class TaskQueryService:
    def __init__(self, tasks: TaskRepository):
        self._tasks = tasks

    async def get_for_user(self, slug: str, current_user: User) -> Task | list[Task]:
        if current_user.role is not RoleCompany.ADMIN:
            team_id = current_user.team_link.team_id
            task = await self._tasks.get_by_slug_for_team(slug, team_id)
            if not task:
                raise LookupError("task_not_found")
            return task
        else:
            tasks = await self._tasks.get_all()
            return list(tasks)


class TaskCommandService:
    def __init__(self, tasks: TaskRepository, users_repo, team_role_getter):
        self._tasks = tasks
        self._users_repo = users_repo
        self._team_role_getter = team_role_getter  # всё, что нужно, можно инжектить

    async def create_task(self, data: TaskCreate, current_user: User) -> Task:
        # проверки ролей и команд можно вынести сюда постепенно
        if (
            current_user.team_link is None
            or current_user.team_link.role is not RoleTeam.MANAGER
        ):
            raise PermissionError("Manager access only")

        team_id = current_user.team_link.team_id

        # тут можно использовать users_repo, чтобы найти исполнителя по email
        assignee = await self._users_repo.get_by_email(data.assignee_email)
        if not assignee:
            raise LookupError("assignee_not_found")

        task = Task(
            id=None,
            assignee_id=assignee.id,
            title=data.title,
            slug="",  # можешь генерить slug на уровне infra/ORM как сейчас
            description=data.description,
            status=TaskStatus(data.status.value),
            deadline=data.deadline,
            team_id=team_id,
        )
        return await self._tasks.add(task)

    async def update_task(self, slug: str, data: TaskUpdate, current_user: User) -> Task:
        if current_user.team_link.role is not RoleTeam.MANAGER:
            raise PermissionError("Manager access only")

        team_id = current_user.team_link.team_id
        task = await self._tasks.get_by_slug_for_team(slug, team_id)
        if not task:
            raise LookupError("task_not_found")

        update_data = data.model_dump(exclude_unset=True)
        # маппинг полей Pydantic -> доменные имена при необходимости
        task = update_task_fields(task, **update_data)
        return await self._tasks.update(task)

    async def delete_task(self, slug: str, current_user: User) -> None:
        if current_user.team_link.role is not RoleTeam.MANAGER:
            raise PermissionError("Manager access only")

        team_id = current_user.team_link.team_id
        task = await self._tasks.get_by_slug_for_team(slug, team_id)
        if not task:
            raise LookupError("task_not_found")

        await self._tasks.delete(task)
