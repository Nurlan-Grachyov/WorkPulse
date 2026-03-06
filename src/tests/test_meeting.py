from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from src.application.routers.router_meeting import (
    add_user_to_meeting,
    create_meeting,
    delete_meeting,
    get_meeting,
)
from src.application.schemas.scheme_meeting import MeetingCreate
from src.infrastructure.db.models.db_meeting import Meeting


@pytest.mark.asyncio
async def test_create_meeting(create_team_with_users, team_manager_user, db_session):
    current_date_plus_one = datetime.now() + timedelta(days=1)

    data_to_meeting = MeetingCreate(
        title="first meeting", starts_at=current_date_plus_one
    )
    meeting = await create_meeting(data_to_meeting, team_manager_user, db_session)

    assert meeting.title == "first meeting"


@pytest.mark.asyncio
async def test_add_user_to_meeting(
    create_team_with_users,
    create_test_meeting,
    team_manager_user,
    usual_user,
    db_session,
):
    meeting = await add_user_to_meeting(
        create_test_meeting.id, usual_user.email, team_manager_user, db_session
    )
    assert meeting == {
        "message": "User added to meeting",
        "meeting_user": {
            "title_meeting": create_test_meeting.title,
            "user_email": usual_user.email,
        },
    }


@pytest.mark.asyncio
async def test_get_meeting(
    create_test_meeting, team_manager_user, admin_user, db_session
):
    meeting = await get_meeting(create_test_meeting.id, admin_user, db_session)
    assert meeting.title == "first meeting"

    meeting = await get_meeting(create_test_meeting.id, team_manager_user, db_session)
    assert meeting.title == "first meeting"


@pytest.mark.asyncio
async def test_delete_meeting(create_test_meeting, admin_user, db_session):
    await delete_meeting(create_test_meeting.id, admin_user, db_session)
    result_deleted_meeting = await db_session.scalars(
        select(Meeting).where(Meeting.id == create_test_meeting.id)
    )
    deleted_meeting = result_deleted_meeting.one_or_none()
    assert deleted_meeting is None
