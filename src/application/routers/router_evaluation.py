from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_active_user
from src.application.routers.router_user import get_user_service
from src.application.schemas.scheme_evaluation import EvaluationCreate, EvaluationGet
from src.application.services.service_evaluations import EvaluationService
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.evaluations.repositories import SqlAlchemyEvaluationRepository
from src.infrastructure.users.repositories import SqlAlchemyUserRepository

evaluation_router = APIRouter(prefix="/evaluations", tags=["evaluations"])


async def get_evaluation_services(
    db: AsyncSession = Depends(get_async_session),
):
    user_repo = SqlAlchemyUserRepository(db)

    evaluation_repo = SqlAlchemyEvaluationRepository(db)
    evaluation_service = EvaluationService(evaluation_repo, user_repo)
    return evaluation_service


@evaluation_router.post(
    "/create_evaluation",
    response_model=EvaluationGet,
    status_code=status.HTTP_201_CREATED,
    summary="Создать оценку задачи",
    description="Создаёт оценку для задачи. Одна оценка на задачу.",
)
async def create_evaluation(
    evaluation: EvaluationCreate,
    current_user: User = Depends(current_active_user),
    evaluation_service=Depends(get_evaluation_services),
) -> EvaluationGet:
    """
    Создать оценку для задачи.

    Ограничения:
    - Для каждой задачи может существовать только одна оценка.
    - Права доступа проверяются политикой RoleBasedEvaluationAccessPolicy.

    Исключения:
    - HTTP 404: Задача не найдена.
    - HTTP 403: Недостаточно прав для создания оценки.
    - HTTP 409: Оценка для этой задачи уже существует.
    - HTTP 500: Ошибка базы данных.
    """
    try:
        db_evaluation = await evaluation_service.create_evaluation(
            current_user, evaluation
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc) or "task_not_found",
        )
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc) or "forbidden",
        )
    except ValueError as exc:
        if "Evaluation for this task already exists" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="evaluation_already_exists",
            )
        if "team_has_dependencies" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="integrity_error",
            )
        raise HTTPException(status_code=400, detail=str(exc) or "bad_request")
    except RuntimeError as exc:
        if "database_error" in str(exc):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="database_error",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="internal_error",
        )

    return EvaluationGet.model_validate(db_evaluation)


@evaluation_router.get(
    "/get_evaluations",
    summary="Получить оценки задач",
    description="Возвращает оценки задач в зависимости от роли пользователя: админ, менеджер, обычный пользователь.",
)
async def get_evaluations(
    current_user: User = Depends(current_active_user),
    evaluation_service=Depends(get_evaluation_services),
    user_service=Depends(get_user_service),
):
    """
    Возвращает агрегированные оценки задач.

    Логика:
    - Админ: видит оценки по всем командам.
    - Менеджер: видит оценки всех участников своей команды (кроме себя).
    - Обычный пользователь: видит только свои задачи и средний балл.

    Исключения:
    - HTTP 404: Пользователь не найден или не привязан к команде.
    - HTTP 500: Ошибка при работе с БД.
    """
    try:
        current_user_with_team_link = await user_service.get_user_with_team_link(
            email=current_user.email
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="user_not_found")

    try:
        evaluations = await evaluation_service.get_evaluations(
            current_user_with_team_link
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc) or "database_error")

    return evaluations
