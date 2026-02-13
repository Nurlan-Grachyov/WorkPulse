from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.db_task import Status


class TaskCreate(BaseModel):
    assignee_email: str
    title: str
    description: Optional[str] = None
    status: Optional[Status] = Status.OPEN
    deadline: datetime

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "assignee_email": "usual@example.com",
                "title": "Создать отчёт",
                "description": "Ежедневный отчёт по продажам",
                "status": "open",
                "deadline": "2026-02-20T18:00:00",
            }
        },
    )


class TaskGet(BaseModel):
    id: int
    assignee_id: UUID
    title: str
    description: Optional[str]
    status: Status
    deadline: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskUpdate(BaseModel):
    assignee_id: Optional[str] = None
    title: Optional[str] = None
    descriptions: Optional[str] = None
    status: Optional[Status] = None
    deadline: Optional[datetime] = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "assignee_email": "usual@example.com",
                "title": "Создать отчёт",
                "description": "Ежедневный отчёт по продажам",
                "status": "open",
                "deadline": "2026-02-20T18:00:00",
            }
        },
    )
