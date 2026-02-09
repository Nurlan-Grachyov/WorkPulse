from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.db_task import Status


class TaskCreate(BaseModel):
    assignee_id: int
    title: str
    description: Optional[str] = None
    status: Optional[Status] = Status.OPEN
    deadline: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "title": "Создать отчёт",
                "description": "Ежедневный отчёт по продажам",
                "status": "open",
                "deadline": "2026-02-10T18:00:00",
            }
        },
    )


class TaskGet(BaseModel):
    id: int
    assignee_id: int
    title: str
    descriptions: Optional[str]
    status: Status
    deadline: datetime


class TaskUpdate(BaseModel):
    assignee_id: Optional[str] = None
    title: Optional[str] = None
    descriptions: Optional[str] = None
    status: Optional[Status] = None
    deadline: Optional[datetime] = None
