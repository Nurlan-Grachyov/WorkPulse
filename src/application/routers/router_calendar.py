from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.auth import current_active_user
from src.application.services.calendar_periods import CalendarPeriodFactory
from src.application.services.service_calendar import CalendarService
from src.infrastructure.calendar.repositories import SqlAlchemyCalendarRepository
from src.infrastructure.db.database import get_async_session
from src.infrastructure.db.models.db_user import User

calendar_router = APIRouter(prefix="/calendar", tags=["calendar"])


async def get_calendar_service(
    db: AsyncSession = Depends(get_async_session),
):
    comment_repo = SqlAlchemyCalendarRepository(db)
    comment_service = CalendarService(comment_repo)
    return comment_service


@calendar_router.get("/")
async def get_info(
    period: str = Query("day", pattern="^(day|month)$"),
    current_user: User = Depends(current_active_user),
    calendar_service=Depends(get_calendar_service),
):
    try:
        period_obj = CalendarPeriodFactory.create(period)
    except ValueError:
        # теоретически не должен сработать, т.к. pattern уже ограничивает
        raise HTTPException(status_code=400, detail="Unsupported period")

    data = await calendar_service.get_info(period_obj, current_user)
    return data
