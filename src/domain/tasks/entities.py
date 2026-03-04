from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.infrastructure.db.models.db_task import Status


@dataclass
class Task:
    assignee_id: int
    title: str
    slug: str
    description: Optional[str]
    status: Status
    deadline: datetime
    team_id: int
