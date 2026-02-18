from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_async_session
from app.models.db_meeting import Meeting
from app.models.db_user import User
from auth import current_active_user

calendar_router = APIRouter(prefix="/calendar", tags=["calendar"])


@calendar_router.get("/")
async def get_info(
    period: str = Query("day", pattern="^(day|month)$"),
    current_user: User = Depends(current_active_user),
    db: AsyncSession = Depends(get_async_session),
):
    today = date.today()

    if period == "day":
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())
    else:  # "month"
        start = today.replace(day=1)
        # простой вариант: +31 дня и обрезать до 1-го
        next_month = (start + timedelta(days=31)).replace(day=1)
        end = datetime.combine(next_month, datetime.min.time())

    result = await db.scalars(
        select(Meeting)
        .join(Meeting.users)
        .where(
            User.id == current_user.id,
            Meeting.starts_at >= start,
            Meeting.starts_at < end,
        )
        .order_by(Meeting.starts_at)
        .options(
            joinedload(Meeting.users).joinedload(
                User.tasks
            ),  # ← Путь: Meeting.users.tasks!
        )
    )
    data = result.unique().all()
    return data
