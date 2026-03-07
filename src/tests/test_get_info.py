import pytest

from src.application.services.calendar_periods import CalendarPeriodFactory
from src.application.services.service_calendar import CalendarService
from src.infrastructure.calendar.repositories import SqlAlchemyCalendarRepository


@pytest.mark.asyncio
async def test_get_info(create_test_meeting, team_manager_user, db_session):
    calendar_repo = SqlAlchemyCalendarRepository(db_session)
    calendar_service = CalendarService(calendar_repo)

    period = CalendarPeriodFactory.create("month")
    info = await calendar_service.get_info(period, team_manager_user)

    assert len(info) == 1
    meeting = info[0]
    assert meeting.title == "first meeting"
