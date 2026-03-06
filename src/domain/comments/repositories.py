from typing import Protocol
from uuid import UUID

from src.infrastructure.db.models.db_comment import Comment


class CommentRepository(Protocol):
    async def save(self, obj) -> None: ...

    async def get_comments_by_task(self, task_id: int): ...

    async def get_comments_by_user(self, user_email: str): ...

    async def get_user_comment_by_id(
        self, comment_id: int, user_id: UUID
    ) -> Comment | None: ...

    async def get_comment_by_id(self, comment_id: int): ...

    async def delete(self, comment: Comment) -> None: ...
