from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.db.models.db_comment import Comment
from src.infrastructure.db.models.db_user import User


class SqlAlchemyCommentRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_comments_by_task(self, task_id: int):
        result = await self._session.scalars(
            select(Comment).where(Comment.task_id == task_id)
        )
        comments = result.all()
        return comments

    async def get_comments_by_user(self, user_email: str):
        result = await self._session.scalars(
            select(Comment).join(Comment.user).where(User.email == user_email)
        )
        comments = result.all()
        return comments

    async def get_user_comment_by_id(
        self, comment_id: int, user_id: UUID
    ) -> Comment | None:
        result = await self._session.scalars(
            select(Comment).where(
                Comment.id == comment_id,
                Comment.user_id == user_id,
            )
        )
        db_comment = result.one_or_none()
        return db_comment

    async def get_comment_by_id(self, comment_id: int) -> Comment | None:
        result = await self._session.scalars(
            select(Comment).where(Comment.id == comment_id)
        )
        return result.one_or_none()

    async def save(self, obj: Comment):
        self._session.add(obj)
        try:
            await self._session.commit()
            await self._session.refresh(obj)
        except IntegrityError as exc:
            await self._session.rollback()
            raise ValueError("integrity_error") from exc
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RuntimeError("db_error") from exc

    async def delete(self, comment: Comment) -> None:
        try:
            await self._session.delete(comment)
            await self._session.commit()
        except SQLAlchemyError as exc:
            await self._session.rollback()
            raise RuntimeError("db_error") from exc
