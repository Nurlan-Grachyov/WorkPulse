import datetime
from typing import Protocol

from src.infrastructure.db.models.db_meeting import Meeting
from src.infrastructure.db.models.db_user import User


class MeetingRepository(Protocol):

    async def check_time_meeting(self, user: User, starts_at: datetime): ...

    async def save(self, meeting) -> None: ...

    async def delete(self, meeting_model: Meeting) -> None: ...

    async def get_meeting_users(self, meeting_id: int): ...

    async def get_meeting(self, meeting_id): ...
