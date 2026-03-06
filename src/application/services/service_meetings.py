from src.application.schemas.scheme_meeting import MeetingCreate
from src.domain.meetings.repositories import MeetingRepository
from src.domain.policies.meeting_permissions import RoleBasedMeetingAccessPolicy
from src.domain.users.repositories import UserRepository
from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_user import User


class MeetingService:
    def __init__(self, meeting: MeetingRepository, user: UserRepository):
        self._meeting = meeting
        self._user = user

    async def create_meeting(self, user: User, meeting: MeetingCreate):
        RoleBasedMeetingAccessPolicy().ensure_can_create(user)
        if await self._meeting.check_time_meeting(user, meeting.starts_at):
            raise LookupError
        created_meeting = Meeting(**meeting.model_dump())
        created_meeting.users.append(user)
        await self._meeting.save(created_meeting)
        return created_meeting

    async def add_user_to_meeting(
        self, current_user: User, user_email: str, meeting_id: int
    ):
        db_meeting = await self._meeting.get_meeting_users(meeting_id)

        if not db_meeting:
            raise LookupError

        RoleBasedMeetingAccessPolicy().ensure_can_update_delete(
            current_user, db_meeting
        )
        db_user = await self._user.get_user(email=user_email)

        if any(user.id == db_user.id for user in db_meeting.users):
            raise PermissionError("User already in meeting")

        db_meeting.users.append(db_user)
        await self._meeting.save(db_meeting)
        return db_meeting, db_user

    async def get_meeting(self, current_user: User, meeting_id: int):
        db_meeting = await self._meeting.get_meeting(meeting_id)
        if not db_meeting:
            raise LookupError("meeting_not_found")

        if RoleBasedMeetingAccessPolicy().can_get_all_meetings(current_user):
            return db_meeting
        else:
            is_participant = any(
                user.id == current_user.id for user in db_meeting.users
            )
            if not is_participant:
                raise LookupError("meeting_not_found")
            return db_meeting

    async def delete_meeting(self, current_user: User, meeting_id: int):
        meeting = await self.get_meeting(current_user, meeting_id)
        if meeting and RoleBasedMeetingAccessPolicy().ensure_can_update_delete(
            current_user, meeting
        ):
            await self._meeting.delete(meeting)
