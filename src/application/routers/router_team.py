from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_superuser
from src.application.routers.router_user import get_user_service
from src.application.schemas.scheme_team import TeamCreate, TeamGet
from src.application.schemas.scheme_user import RoleTeam, UserReadWithTeamRole
from src.application.services.service_teams import TeamService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.teams.repositories import SqlAlchemyTeamRepository

team_router = APIRouter(tags=["teams"], prefix="/team")


async def get_team_service(
    db: AsyncSession = Depends(get_async_session),
) -> TeamService:
    """
    Возвращает сервис работы с командами.

    Создаёт репозиторий команд на основе текущей async-сессии БД
    и оборачивает его в слой бизнес-логики TeamService.
    """
    team_repo = SqlAlchemyTeamRepository(db)
    team_service = TeamService(team_repo)
    return team_service


@team_router.post(
    "/create_team",
    response_model=TeamGet,
    status_code=201,
    summary="Создать новую команду",
    description="Создаёт новую команду с уникальным названием. Доступно только суперпользователю.",
)
async def create_team(
    team_in: TeamCreate,
    superuser: User = Depends(current_superuser),
    service=Depends(get_team_service),
) -> TeamGet:
    """
    Создаёт новую команду в системе.

    Проверки:
    - Название команды (`title_team`) должно быть уникальным.
    - Доступ к операции есть только у суперпользователя.

    Возвращает:
    - Схему TeamGet с данными созданной команды (включая slug).
    """
    try:
        team = await service.create_team(team_in)
        return TeamGet.model_validate(team)
    except ValueError as exc:
        if "team_exists" in str(exc):
            raise HTTPException(status_code=409, detail="team_already_exists")
        raise HTTPException(status_code=400, detail="bad_request")
    except SQLAlchemyError:
        raise HTTPException(status_code=500, detail="try_later")


@team_router.get(
    "/{slug_team}/users/",
    status_code=200,
    summary="Получить всех пользователей команды",
    description="Возвращает список пользователей команды с предзагруженными задачами и комментариями. "
    "Доступно только суперпользователю.",
)
async def get_users_of_team(
    slug_team: str,
    superuser: User = Depends(current_superuser),
    service=Depends(get_team_service),
) -> List[UserReadWithTeamRole]:
    """
    Получить список пользователей конкретной команды.

    Особенности:
    - Используется жадная загрузка (selectinload) задач и комментариев пользователя.
    - Выполняется JOIN через таблицу связей TeamUser.
    - Операция доступна только суперпользователю.

    Возвращает:
    - Список схем UserReadWithTeamRole для всех пользователей команды.
    """
    try:
        users = await service.get_users_of_team(slug_team)
        return [UserReadWithTeamRole.model_validate(user) for user in users]
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )


@team_router.post(
    "/{slug_team}/users/add_user/",
    status_code=201,
    summary="Добавить пользователя в команду",
    description="Добавляет существующего пользователя в команду с указанной ролью. Доступно только суперпользователю.",
)
async def add_user_to_team(
    slug_team: str,
    user_email: str,
    role: RoleTeam,
    superuser: User = Depends(current_superuser),
    user_service=Depends(get_user_service),
    team_service=Depends(get_team_service),
):
    """
    Добавляет пользователя в команду, создавая запись связи TeamUser.

    Проверки:
    1. Пользователь с указанным email существует.
    2. Команда с указанным slug существует.
    3. Пользователь ещё не состоит в этой команде (уникальность пары user_id+team_id).

    Возвращает:
    - Данные созданной связи команда–пользователь (TeamUser) в виде ORM-объекта или схемы
    (в зависимости от реализации).
    """
    try:
        user = await user_service.get_user(email=user_email)
    except LookupError:
        raise HTTPException(status_code=404, detail=f"User {user_email} not found")

    try:
        new_team_user = await team_service.add_user_to_team(slug_team, user.id, role)
        return new_team_user
    except ValueError:
        raise HTTPException(
            status_code=409,
            detail="The user already exists in the team",
        )
    except LookupError:
        raise HTTPException(
            status_code=404,
            detail=f"Team {slug_team} not found",
        )


@team_router.patch(
    "/{slug_team}/users/{slug_user}/role/",
    status_code=200,
    summary="Изменить роль пользователя в команде",
    description="Изменяет роль пользователя в команде с учётом бизнес-правила «только один менеджер в команде». "
    "Доступно только суперпользователю.",
)
async def change_role_user(
    slug_team: str,
    slug_user: str,
    role_data: RoleTeam,
    user_service=Depends(get_user_service),
    team_service=Depends(get_team_service),
    superuser: User = Depends(current_superuser),
):
    """
    Изменяет роль пользователя в команде, соблюдая правило «один менеджер на команду».

    Логика для роли MANAGER:
    1. Понизить всех текущих менеджеров команды (кроме целевого пользователя) до роли USER.
    2. Назначить целевому пользователю роль MANAGER.

    Для остальных ролей:
    - Выполняется обычная смена роли без побочных эффектов.

    Возвращает:
    - Обновлённый объект связи TeamUser или соответствующую схему с новой ролью.
    """
    try:
        user = await user_service.get_user(slug=slug_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="user_not_found")

    try:
        new_role = await team_service.change_role_user(
            slug_team=slug_team, user=user, role_data=role_data
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),  # например: "user_not_in_team" или "team_not_found"
        )
    except ValueError as exc:
        if "integrity_error" in str(exc):
            raise HTTPException(status_code=409, detail="integrity_violation")
        raise HTTPException(status_code=400, detail="bad_request")
    except RuntimeError as exc:
        if "db_error" in str(exc):
            raise HTTPException(status_code=500, detail="database_error")
        raise HTTPException(status_code=500, detail="internal_error")
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="unexpected_error")

    return new_role


@team_router.delete(
    "/{slug_team}/",
    status_code=204,
    summary="Удалить команду",
    description="Удаляет команду по slug. Доступно только суперпользователю. "
    "Нельзя удалить команду, от которой зависят другие сущности (FK).",
)
async def delete_team(
    slug_team: str,
    superuser: User = Depends(current_superuser),
    team_service=Depends(get_team_service),
) -> None:
    """
    Удаляет команду по её slug с обработкой ошибок целостности данных.

    Проверки/ограничения:
    - Если команда не найдена — возвращается 404.
    - Если у команды есть зависимые сущности (например, пользователи, задачи) и БД не позволяет удалить её
      из-за ограничений внешних ключей — возвращается 409.
    - При любых других ошибках БД возвращается 500.

    Возвращает:
    - 204 No Content при успешном удалении.
    """
    try:
        await team_service.delete_team(slug_team)
    except ValueError as exc:
        if "team_not_found" in str(exc) or "not_found" in str(exc):
            raise HTTPException(status_code=404, detail="team_not_found")
        if "dependencies" in str(exc):
            raise HTTPException(status_code=409, detail="team_has_dependencies")
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as e:
        print(e)
        raise HTTPException(status_code=500, detail="database_error")
