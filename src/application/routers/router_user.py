from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_active_user, current_superuser
from src.application.schemas.scheme_user import UserRead, UserUpdate
from src.application.services.service_users import UserService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.users.repositories import SqlAlchemyUserRepository

user_router = APIRouter(tags=["users"], prefix="/users")


async def get_user_service(
    db: AsyncSession = Depends(get_async_session),
) -> UserService:
    """
    Возвращает сервис пользователей с подключённым репозиторием.

    Используется как зависимость в роутерах для инкапсуляции доступа к БД.
    """
    user_repo = SqlAlchemyUserRepository(db)
    return UserService(user_repo)


@user_router.get(
    "/all_users/",
    response_model=list[UserRead],
    status_code=200,
    summary="Получить всех пользователей",
    description="Возвращает список всех пользователей. Доступно любому авторизованному пользователю.",
)
async def get_users(
    current_active_user: User = Depends(current_active_user),
    user_service=Depends(get_user_service),
) -> list[UserRead]:
    """
    Получить список всех пользователей.

    Возвращает упрощённое представление пользователей (схема UserRead)
    для отображения в списках/таблицах на клиенте.
    """
    try:
        users = await user_service.get_users()
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    return [UserRead.model_validate(user) for user in users]


@user_router.get(
    "/{slug}/",
    response_model=UserRead,
    status_code=200,
    summary="Получить пользователя по slug",
    description="Возвращает пользователя с информацией о команде и участниках. "
    "Доступно любому авторизованному пользователю.",
)
async def get_user(
    slug: str,
    current_active_user: User = Depends(current_active_user),
    user_service=Depends(get_user_service),
) -> UserRead:
    """
    Получить подробную информацию о пользователе по его slug.

    В ответе возвращается схема UserRead, включающая базовые данные пользователя
    и информацию о его принадлежности к команде.
    """
    user = await user_service.get_user(slug=slug)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserRead.model_validate(user)


@user_router.patch(
    "/{user_email}/",
    response_model=UserRead,
    status_code=200,
    summary="Обновить глобальную роль пользователя",
    description="Обновляет глобальную роль пользователя в компании. Доступно только суперпользователю.",
)
async def update_user(
    user_email: str,
    data_for_update_user: UserUpdate,
    superuser: User = Depends(current_superuser),
    user_service=Depends(get_user_service),
) -> UserRead:
    """
    Обновляет глобальную роль пользователя в компании.

    Обновляется поле `role` в модели User (роль на уровне компании, а не команды).
    Требуется авторизация суперпользователя.

    Проверки:
    - Пользователь с указанным email существует.
    - Пользователь активен.
    - Текущий пользователь имеет права суперпользователя.

    Возвращает:
    - Обновлённую схему UserRead с новой ролью.
    """
    try:
        data_for_update_user = data_for_update_user.model_dump(exclude_unset=True)
        user = await user_service.update_user(user_email, data_for_update_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserRead.model_validate(user)


@user_router.delete(
    "/{user_email}/",
    status_code=204,
    summary="Удалить пользователя по email",
    description="Удаляет пользователя по email. Доступно только суперпользователю. Нельзя удалить суперпользователей.",
)
async def delete_user(
    user_email: str,
    superuser: User = Depends(current_superuser),
    user_service=Depends(get_user_service),
) -> None:
    """
    Удаляет пользователя по email с дополнительными проверками безопасности.

    Проверки:
    - Пользователь с указанным email существует.
    - Нельзя удалить учётную запись суперпользователя.
    - Корректно удаляются связанные записи (в рамках реализованной логики сервиса).

    Возвращает:
    - 204 No Content при успешном удалении.
    """
    try:
        await user_service.delete_user(user_email)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
