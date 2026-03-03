from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth import current_active_user
from src.application.schemas.scheme_task import TaskCreate, TaskGet, TaskUpdate
from src.application.services.service_tasks import TaskCommandService, TaskQueryService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository

task_router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_services(
    db: AsyncSession = Depends(get_async_session),
) -> tuple[TaskQueryService, TaskCommandService]:
    task_repo = SqlAlchemyTaskRepository(db)
    # users_repo и team_role_getter можно собрать аналогично из infrastructure
    users_repo = ...
    team_role_getter = ...
    query_service = TaskQueryService(task_repo)
    command_service = TaskCommandService(task_repo, users_repo, team_role_getter)
    return query_service, command_service


@task_router.get(
    "/{slug}",
    response_model=TaskGet | list[TaskGet],
    status_code=200,
)
async def get_task(
    slug: str,
    current_user: User = Depends(current_active_user),
    services=Depends(get_task_services),
):
    query_service, _ = services
    try:
        result = await query_service.get_for_user(slug, current_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    if isinstance(result, list):
        return [TaskGet.model_validate(t) for t in result]
    return TaskGet.model_validate(result)


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
    _, command_service = services
    try:
        created = await command_service.create_task(task, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    return TaskGet.model_validate(created)


@task_router.patch(
    "/{slug}",
    response_model=TaskGet,
    status_code=200,
)
async def update_task(
    slug: str,
    task: TaskUpdate,
    current_user: User = Depends(current_active_user),
    services=Depends(get_task_services),
):
    _, command_service = services
    try:
        updated = await command_service.update_task(slug, task, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskGet.model_validate(updated)


@task_router.delete(
    "/{slug}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    slug: str,
    current_user: User = Depends(current_active_user),
    services=Depends(get_task_services),
):
    _, command_service = services
    try:
        await command_service.delete_task(slug, current_user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")
