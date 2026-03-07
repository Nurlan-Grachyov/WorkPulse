from src.application.schemas.scheme_comment import CommentCreate, CommentUpdate
from src.domain.comments.repositories import CommentRepository
from src.domain.comments.services import update_comment_fields
from src.domain.policies.global_permissions import is_admin
from src.domain.tasks.repositories import TaskRepository
from src.infrastructure.db.models.db_comment import Comment
from src.infrastructure.db.models.db_user import User


class CommentService:
    def __init__(self, comment: CommentRepository, task: TaskRepository):
        self._comment = comment
        self._task = task

    async def create_comment(
        self, comment: CommentCreate, current_user: User
    ) -> Comment:
        await self._task.get_task_by_id(comment.task_id)
        comment = Comment(**comment.model_dump(), user_id=current_user.id)
        await self._comment.save(comment)
        return comment

    async def get_comments_by_task(self, task_id: int):
        return await self._comment.get_comments_by_task(task_id)

    async def get_comments_by_user(self, user_email: str):
        return await self._comment.get_comments_by_user(user_email)

    async def update_comment(
        self, comment_id: int, comment_to_update: CommentUpdate, current_user: User
    ):
        comment = await self._comment.get_user_comment_by_id(
            comment_id, current_user.id
        )
        if comment is None:
            raise LookupError("comment_not_found")
        update_data = comment_to_update.model_dump(exclude_unset=True)
        updated_comment = update_comment_fields(comment, update_data)
        try:
            await self._comment.save(updated_comment)
        except ValueError:
            raise ValueError("invalid_comment_state")
        return updated_comment

    async def delete_comment(self, comment_id: int, current_user: User) -> None:
        comment = await self._comment.get_comment_by_id(comment_id)
        if comment is None:
            raise LookupError("comment_not_found")

        # автор или админ может удалить
        if not (is_admin(current_user) or comment.user_id == current_user.id):
            raise PermissionError("cannot_delete_comment")

        try:
            await self._comment.delete(comment)
        except RuntimeError:
            # пробрасываем выше, роутер превратит в 500
            raise
