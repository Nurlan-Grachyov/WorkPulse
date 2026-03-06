from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_active_user
from src.application.routers.router_user import get_user_service
from src.application.schemas.scheme_meeting import MeetingCreate, MeetingGet
from src.application.schemas.scheme_user import UserRead
from src.application.services.service_meetings import MeetingService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.meetings.repositories import SqlAlchemyMeetingRepository
from src.infrastructure.users.repositories import SqlAlchemyUserRepository

meeting_router = APIRouter(prefix="/meetings", tags=["meetings"])


async def get_meeting_service(
    db: AsyncSession = Depends(get_async_session),
) -> MeetingService:
    """
    Возвращает сервис для работы со встречами.

    Создаёт репозиторий встреч и репозиторий пользователей, передаёт их в сервис MeetingService.
    Используется как зависимость во всех эндпоинтах, связанных со встречами.
    """
    user_repo = SqlAlchemyUserRepository(db)
    meet_repo = SqlAlchemyMeetingRepository(db)
    meet_service = MeetingService(meet_repo, user_repo)
    return meet_service


@meeting_router.post(
    "/create_meeting",
    response_model=MeetingGet,
    status_code=status.HTTP_201_CREATED,
    summary="Создать встречу",
    description="Менеджеры и администраторы могут создавать встречи. "
    "Проверяется пересечение по времени в пределах команды.",
)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: User = Depends(current_active_user),
    meeting_service=Depends(get_meeting_service),
    user_service=Depends(get_user_service),
) -> MeetingGet:
    """
    Создать новую встречу с проверкой роли и пересечения по времени.

    Проверки:
    - Пользователь существует и активен.
    - Пользователь имеет достаточные права (менеджер команды или администратор компании).
    - В команде нет другой встречи в тот же временной слот.

    Исключения:
    - HTTP 404: Пользователь не найден.
    - HTTP 403: Недостаточно прав (не менеджер и не администратор).
    - HTTP 409: В указанное время уже существует встреча в этой команде.

    Возвращает:
    - Схему MeetingGet с данными созданной встречи.
    """
    try:
        user = await user_service.get_user_with_team_link(email=current_user.email)
    except LookupError:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        created_meeting = await meeting_service.create_meeting(user, meeting)
    except LookupError:
        raise HTTPException(
            status_code=409,
            detail="A meeting at this time already exists",
        )

    return MeetingGet.model_validate(created_meeting)


@meeting_router.post(
    "/{meeting_id}/users/add_user/",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Добавить пользователя на встречу",
    description="Добавляет существующего пользователя в список участников встречи.",
)
async def add_user_to_meeting(
    meeting_id: int,
    user_email: str,
    current_user: User = Depends(current_active_user),
    meeting_service=Depends(get_meeting_service),
) -> UserRead:
    """
    Добавить пользователя в участники встречи.

    Проверки:
    - Встреча существует.
    - Пользователь с указанным email существует.
    - Текущий пользователь имеет право добавлять участников (логика внутри сервиса).
    - Пользователь ещё не добавлен в эту встречу.

    Возвращает:
    - Схему UserRead для добавленного участника.
    """
    db_meeting, db_user = await meeting_service.add_user_to_meeting(
        current_user, user_email, meeting_id
    )
    return UserRead.model_validate(db_user)


@meeting_router.get(
    "/{meeting_id}",
    response_model=MeetingGet,
    summary="Получить встречу по id",
    description="Администраторы видят любые встречи. "
    "Остальные пользователи видят только встречи, в которых участвуют.",
)
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(current_active_user),
    meeting_service=Depends(get_meeting_service),
) -> MeetingGet:
    """
    Получить встречу по её идентификатору с учётом прав доступа.

    Логика доступа:
    - Администратор компании может просматривать любые встречи.
    - Остальные пользователи могут видеть только те встречи, где они являются участниками.
    - Для скрытия факта существования встречи при отсутствии прав возвращается 404.

    Параметры:
    - meeting_id: идентификатор встречи (path-параметр).

    Исключения:
    - HTTP 404: Встреча не найдена или доступ к ней запрещён.

    Возвращает:
    - Схему MeetingGet с подробной информацией о встрече.
    """
    try:
        db_meeting = await meeting_service.get_meeting(current_user, meeting_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "meeting_not_found",
        )
    return MeetingGet.model_validate(db_meeting)


@meeting_router.delete(
    "/{meeting_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить встречу",
    description=(
        "Администратор компании может удалить любую встречу. "
        "Менеджер команды может удалить только встречи, в которых сам участвует. "
        "Связи с участниками (meeting_participants) удаляются каскадно."
    ),
)
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(current_active_user),
    meeting_service=Depends(get_meeting_service),
) -> None:
    """
    Удалить встречу с жёсткой проверкой прав доступа.

    Логика авторизации:
    - Администратор компании: может удалять любые встречи.
    - Менеджер команды: может удалять только те встречи, в которых он является участником.
    - Прочие пользователи: не имеют права на удаление (ошибка 403 внутри сервиса
      может быть замаскирована под LookupError для возврата 404).

    Исключения:
    - HTTP 404: Встреча не найдена или пользователь не имеет права видеть/удалять её
      (в зависимости от политики сокрытия).
    - HTTP 403: Может использоваться, если явно разделяешь «нет доступа» и «не найдено».

    Примечания:
    - Благодаря настройке cascade в ORM-связях, при удалении встречи автоматически
      удаляются записи в таблице связей участников.

    Возвращает:
    - 204 No Content при успешном удалении.
    """
    try:
        await meeting_service.delete_meeting(current_user, meeting_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "meeting_not_found",
        )

    return None  # 204 No Content
