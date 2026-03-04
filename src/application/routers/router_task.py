from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth import current_active_user
from src.application.schemas.scheme_task import TaskCreate, TaskGet, TaskUpdate
from src.application.services.service_tasks import TaskService
from src.application.services.service_users import UserService
from src.domain.policies.task_creation import ManagerOnlyTaskCreationPolicy
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository
from src.infrastructure.users.repositories import SqlAlchemyUserRepository

task_router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_services(
        db: AsyncSession = Depends(get_async_session),
) -> tuple[TaskService, UserService]:
    task_repo = SqlAlchemyTaskRepository(db)
    policy = ManagerOnlyTaskCreationPolicy()

    users_repo = SqlAlchemyUserRepository(db)
    user_service = UserService(users_repo)

    task_service = TaskService(task_repo, policy)
    return task_service, user_service


@task_router.get(
    "/{slug}",
    response_model=TaskGet,
    status_code=200,
)
async def get_task(
        slug_task: str,
        current_user: User = Depends(current_active_user),
        services=Depends(get_task_services),
):
    task_service, user_service = services
    try:
        task =  await task_service.get_task_by_slug_for_team(slug_task)
        return TaskGet.model_validate(task)
    except LookupError:
        raise HTTPException(404, detail="User not found")


@task_router.post(
    "/create_task",
    response_model=TaskGet,
    status_code=201,
)
async def create_task(
        task: TaskCreate,
        current_user: User = Depends(current_active_user),
        services=Depends(get_task_services),
):
    task_service, user_service = services

    created_task = await task_service.add_task(task, current_user)
    return TaskGet.model_validate(created_task)

@task_router.patch(
    "/{slug}",
    response_model=TaskGet,
    status_code=200,
)
async def update_task(
        slug_task: str,
        task: TaskUpdate,
        current_user: User = Depends(current_active_user),
        services=Depends(get_task_services),
):
    task_service, user_service = services
    update_data = task.model_dump(exclude_unset=True)

    updated_task = await task_service.update_task(slug_task, update_data, current_user)
    return TaskGet.model_validate(updated_task)

@task_router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
        slug_task: str,
        current_user: User = Depends(current_active_user),
        services=Depends(get_task_services),
):
    task_service, user_service = services

    await task_service.delete_task(slug_task, current_user)
