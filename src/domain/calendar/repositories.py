from datetime import datetime
from typing import Protocol
from uuid import UUID


class CalendarRepository(Protocol):
    async def get_info_for_range(
        self, user_id: UUID, start: datetime, end: datetime
    ): ...
