from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROCESS = "in process"
    DONE = "done"


@dataclass
class Task:
    id: int | None
    assignee_id: int
    title: str
    slug: str
    description: Optional[str]
    status: TaskStatus
    deadline: datetime
    team_id: int
