import pytest

from src.application.routers.router_calendar import get_info


@pytest.mark.asyncio
async def test_get_info(create_test_meeting, team_manager_user, db_session):
    info = await get_info("month", team_manager_user, db_session)

    assert len(info) == 1
    meeting = info[0]
    assert meeting.title == "first meeting"
