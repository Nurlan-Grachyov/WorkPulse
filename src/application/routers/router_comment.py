from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.application.auth import current_active_user
from src.application.schemas.scheme_comment import (
    CommentCreate,
    CommentGet,
    CommentUpdate,
)
from src.application.services.service_comments import CommentService
from src.infrastructure.comments.repositories import SqlAlchemyCommentRepository
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User
from src.infrastructure.tasks.repositories import SqlAlchemyTaskRepository

comment_router = APIRouter(prefix="/comments", tags=["comments"])


async def get_comment_services(
    db: AsyncSession = Depends(get_async_session),
) -> CommentService:
    task_repo = SqlAlchemyTaskRepository(db)
    comment_repo = SqlAlchemyCommentRepository(db)
    comment_service = CommentService(comment_repo, task_repo)
    return comment_service


@comment_router.post(
    "/create_comment",
    response_model=CommentGet,
    status_code=201,
    summary="Создать новый комментарий",
    description=(
        "Создаёт новый комментарий к конкретной задаче. "
        "Аутентифицированные пользователи могут создавать комментарии "
        "только к задачам, к которым у них есть доступ."
    ),
)
async def create_comment(
    comment: CommentCreate,
    current_user: User = Depends(current_active_user),
    service: CommentService = Depends(get_comment_services),
) -> CommentGet:
    """
    Создаёт новый комментарий от имени текущего пользователя.
    """
    try:
        created_comment = await service.create_comment(comment, current_user)
    except LookupError:
        raise HTTPException(status_code=404, detail="Task not found")

    return CommentGet.model_validate(created_comment)


@comment_router.get(
    "/tasks/{task_id}",
    response_model=list[CommentGet],
    status_code=200,
    summary="Получить комментарии по ID задачи",
    description=(
        "Возвращает все комментарии для заданной задачи "
        "с жадной загрузкой автора и связанной задачи."
    ),
)
async def get_comments_by_task(
    task_id: int,
    current_user: User = Depends(current_active_user),
    service: CommentService = Depends(get_comment_services),
) -> list[CommentGet]:
    """
    Получить список комментариев для конкретной задачи.
    """
    comments = await service.get_comments_by_task(task_id)
    return [CommentGet.model_validate(comment) for comment in comments]


@comment_router.get(
    "/users/",
    response_model=list[CommentGet],
    status_code=200,
    summary="Получить комментарии по email пользователя",
    description=(
        "Возвращает все комментарии, созданные указанным пользователем. "
        "Фильтрация выполняется через JOIN по связи с пользователем."
    ),
)
async def get_comments_by_user(
    user_email: str,
    current_user: User = Depends(current_active_user),
    service: CommentService = Depends(get_comment_services),
) -> list[CommentGet]:
    """
    Получить комментарии, созданные пользователем по его email.
    """
    comments = await service.get_comments_by_user(user_email)
    return [CommentGet.model_validate(comment) for comment in comments]


@comment_router.patch(
    "/{comment_id}",
    response_model=CommentGet,
    status_code=200,
    summary="Обновить комментарий",
    description=(
        "Обновляет существующий комментарий. "
        "Только автор комментария может изменять свой комментарий. "
        "Поддерживаются частичные обновления (PATCH)."
    ),
)
async def update_comment(
    comment_id: int,
    comment: CommentUpdate,
    current_user: User = Depends(current_active_user),
    service: CommentService = Depends(get_comment_services),
) -> CommentGet:
    """
    Обновить существующий комментарий.
    """
    try:
        updated_comment = await service.update_comment(
            comment_id, comment, current_user
        )
    except LookupError:
        raise HTTPException(status_code=404, detail="Comment not found")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid comment data",
        )

    return CommentGet.model_validate(updated_comment)


@comment_router.delete(
    "/{comment_id}",
    response_model=None,
    summary="Удалить комментарий",
    description=(
        "Удаляет комментарий по его ID. "
        "Доступно автору комментария и администраторам."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(current_active_user),
    service: CommentService = Depends(get_comment_services),
) -> None:
    """
    Удалить комментарий.
    """
    try:
        await service.delete_comment(comment_id, current_user)
    except LookupError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden",
        )
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
