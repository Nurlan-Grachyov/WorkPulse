from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.domain.meetings.repositories import MeetingRepository
from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_team import TeamUser
from src.infrastructure.db.models.db_user import User


class SqlAlchemyMeetingRepository(MeetingRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def check_time_meeting(self, user: User, starts_at: datetime):
        team_id = user.team_link.team_id

        result_meeting = await self._session.scalars(
            select(Meeting)
            .join(Meeting.users)  # join через secondary meeting_participants
            .join(User.team_link)  # join к TeamUser
            .where(
                Meeting.starts_at == starts_at,
                TeamUser.team_id == team_id,
            )
            .options(
                joinedload(Meeting.users),
            )
        )

        conflicting_meetings = result_meeting.one_or_none()
        return conflicting_meetings

    async def get_meeting_users(self, meeting_id: int):
        result = await self._session.scalars(
            select(Meeting)
            .options(
                joinedload(Meeting.users).joinedload(
                    User.team_link
                )  # Eager load avoids lazy loading
            )
            .where(Meeting.id == meeting_id)
        )
        db_meeting = result.unique().one_or_none()

        return db_meeting

    async def get_meeting(self, meeting_id):
        result_meeting = await self._session.scalars(
            select(Meeting)
            .options(joinedload(Meeting.users))
            .where(Meeting.id == meeting_id)
        )
        db_meeting = result_meeting.unique().one_or_none()

        return db_meeting

    async def save(self, meeting) -> None:
        self._session.add(meeting)
        await self._session.commit()
        await self._session.refresh(meeting)

    async def delete(self, meeting_model: Meeting) -> None:
        await self._session.delete(meeting_model)
        await self._session.commit()
