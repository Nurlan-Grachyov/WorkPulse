from datetime import date

from src.domain.calendar.repositories import CalendarRepository
from src.domain.calendar.service import CalendarPeriod
from src.infrastructure.db.models.db_user import User


class CalendarService:
    def __init__(self, calendar: CalendarRepository):
        self._calendar = calendar

    async def get_info(self, period: CalendarPeriod, current_user: User):
        today = date.today()
        start, end = period.get_range(today)
        # один метод в репозитории вместо двух почти одинаковых
        return await self._calendar.get_info_for_range(current_user.id, start, end)
