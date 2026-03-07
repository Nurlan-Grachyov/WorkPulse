from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_user import User


class SqlAlchemyCalendarRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_info_for_range(self, user_id: UUID, start: datetime, end: datetime):
        result = await self._session.scalars(
            select(Meeting)
            .join(Meeting.users)
            .where(
                User.id == user_id,
                Meeting.starts_at >= start,
                Meeting.starts_at < end,
            )
            .order_by(Meeting.starts_at)
            .options(
                joinedload(Meeting.users).joinedload(User.tasks),
            )
        )
        return result.unique().all()
