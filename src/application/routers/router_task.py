from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth import current_active_user
from src.application.schemas.scheme_task import TaskCreate, TaskGet, TaskUpdate
from src.application.services.service_tasks import TaskService
from src.domain.policies.task_permissions import RoleBasedTaskAccessPolicy
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository

task_router = APIRouter(prefix="/tasks", tags=["tasks"])


async def get_task_services(
    db: AsyncSession = Depends(get_async_session),
) -> TaskService:
    """
    Возвращает сервисы задач и пользователей, основанные на общей async-сессии БД.

    Создаёт:
    - репозиторий задач и оборачивает его в TaskService с политикой доступа;
    - репозиторий пользователей и оборачивает его в UserService.

    Используется как зависимость в роутерах задач.
    """
    task_repo = SqlAlchemyTaskRepository(db)
    policy = RoleBasedTaskAccessPolicy()

    task_service = TaskService(task_repo, policy)
    return task_service


@task_router.get(
    "/{slug_task}",
    response_model=TaskGet,
    status_code=200,
    summary="Получить задачу по slug",
    description="Возвращает задачу по slug с учётом прав доступа пользователя.",
)
async def get_task(
    slug_task: str,
    current_user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_services),
) -> TaskGet:
    """
    Получить одну задачу по её slug.

    Доступ:
    - Конкретные права определяются политикой RoleBasedTaskAccessPolicy внутри сервиса.

    Возвращает:
    - Схему TaskGet с подробной информацией о задаче.
    """
    try:
        task = await service.get_task_by_slug_for_team(slug_task)
        return TaskGet.model_validate(task)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")


@task_router.get(
    "/",
    response_model=list[TaskGet],
    status_code=200,
    summary="Получить список задач",
    description="Возвращает список задач, доступных текущему пользователю.",
)
async def get_all_task(
    current_user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_services),
) -> list[TaskGet]:
    """
    Получить список всех задач, доступных текущему пользователю.

    Фактический набор задач определяется политикой доступа и реализацией сервиса задач.
    Возвращаются только те задачи, которые пользователь имеет право видеть.

    Возвращает:
    - Список схем TaskGet.
    """

    tasks = await service.get_all_task(current_user)
    return [TaskGet.model_validate(task) for task in tasks]


@task_router.post(
    "/create_task",
    response_model=TaskGet,
    status_code=201,
    summary="Создать задачу",
    description="Создаёт новую задачу с учётом прав доступа и уникальности slug.",
)
async def create_task(
    task: TaskCreate,
    current_user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_services),
) -> TaskGet:
    """
    Создать новую задачу.

    Проверки:
    - Текущий пользователь имеет право создавать задачи (по политике RoleBasedTaskAccessPolicy).
    - Исполнитель задачи существует (если указан).
    - Slug задачи уникален.

    Возвращает:
    - Схему TaskGet для только что созданной задачи.
    """
    try:
        data = task.model_dump(exclude_unset=True)
        created_task = await service.add_task(data, current_user)
        print("router")
        return TaskGet.model_validate(created_task)
    except PermissionError:
        raise HTTPException(
            status_code=409,
            detail="You dont have enough rights",
        )
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail="Assignee is not found",
        )
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="Task`s slug already exists",
        )


@task_router.patch(
    "/{slug_task}",
    response_model=TaskGet,
    status_code=200,
    summary="Обновить задачу",
    description="Обновляет поля задачи по slug с учётом прав доступа текущего пользователя.",
)
async def update_task(
    slug_task: str,
    task: TaskUpdate,
    current_user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_services),
) -> TaskGet:
    """
    Обновить существующую задачу по её slug.

    Проверки:
    - Задача существует.
    - Текущий пользователь имеет право изменять эту задачу
      (например, автор, исполнитель или администратор команды/системы).

    Обновляются только те поля, которые переданы (partial update).

    Возвращает:
    - Обновлённую схему TaskGet.
    """
    try:
        update_data = task.model_dump(exclude_unset=True)

        updated_task = await service.update_task(slug_task, update_data, current_user)
        return TaskGet.model_validate(updated_task)
    except LookupError:
        raise HTTPException(
            status_code=409,
            detail="You dont have enough rights",
        )


@task_router.delete(
    "/{slug_task}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить задачу",
    description="Удаляет задачу по slug с учётом прав доступа текущего пользователя.",
)
async def delete_task(
    slug_task: str,
    current_user: User = Depends(current_active_user),
    service: TaskService = Depends(get_task_services),
) -> None:
    """
    Удалить задачу по её slug.

    Проверки:
    - Задача существует.
    - Текущий пользователь имеет достаточные права для удаления задачи
      (например, автор, владелец команды или администратор в соответствии с политикой доступа).

    Возвращает:
    - 204 No Content при успешном удалении.
    """
    try:
        await service.delete_task(slug_task, current_user)
    except LookupError:
        raise HTTPException(
            status_code=409,
            detail="You dont have enough rights",
        )
