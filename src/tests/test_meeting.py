from datetime import datetime, timedelta

import pytest
from sqlalchemy import select

from src.application.schemas.scheme_meeting import MeetingCreate
from src.application.services.service_meetings import MeetingService
from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.meetings.repositories import SqlAlchemyMeetingRepository
from src.infrastructure.users.repositories import SqlAlchemyUserRepository


@pytest.mark.asyncio
async def test_create_meeting(create_team_with_users, team_manager_user, db_session):
    user_repo = SqlAlchemyUserRepository(db_session)
    meeting_repo = SqlAlchemyMeetingRepository(db_session)
    meeting_service = MeetingService(meeting_repo, user_repo)

    current_date_plus_one = datetime.now() + timedelta(days=1)

    data_to_meeting = MeetingCreate(
        title="first meeting", starts_at=current_date_plus_one
    )
    meeting = await meeting_service.create_meeting(team_manager_user, data_to_meeting)

    assert meeting.title == "first meeting"


@pytest.mark.asyncio
async def test_add_user_to_meeting(
    create_team_with_users,
    create_test_meeting,
    team_manager_user,
    usual_user,
    db_session,
):
    user_repo = SqlAlchemyUserRepository(db_session)
    meeting_repo = SqlAlchemyMeetingRepository(db_session)
    meeting_service = MeetingService(meeting_repo, user_repo)

    db_meeting, db_user = await meeting_service.add_user_to_meeting(
        team_manager_user, usual_user.email, create_test_meeting.id
    )
    assert db_meeting.title == "first meeting"
    assert db_user.role == "user"


@pytest.mark.asyncio
async def test_get_meeting(
    create_test_meeting, team_manager_user, admin_user, db_session
):
    user_repo = SqlAlchemyUserRepository(db_session)
    meeting_repo = SqlAlchemyMeetingRepository(db_session)
    meeting_service = MeetingService(meeting_repo, user_repo)

    meeting = await meeting_service.get_meeting(admin_user, create_test_meeting.id)
    assert meeting.title == "first meeting"

    meeting = await meeting_service.get_meeting(
        team_manager_user, create_test_meeting.id
    )
    assert meeting.title == "first meeting"


@pytest.mark.asyncio
async def test_delete_meeting(create_test_meeting, team_manager_user, db_session):
    user_repo = SqlAlchemyUserRepository(db_session)
    meeting_repo = SqlAlchemyMeetingRepository(db_session)
    meeting_service = MeetingService(meeting_repo, user_repo)

    await meeting_service.delete_meeting(team_manager_user, create_test_meeting.id)
    result_deleted_meeting = await db_session.scalars(
        select(Meeting).where(Meeting.id == create_test_meeting.id)
    )
    deleted_meeting = result_deleted_meeting.one_or_none()
    assert deleted_meeting is None
