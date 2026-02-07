from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.db_task import Status


class TaskCreate(BaseModel):
    user_id: int
    title: str
    descriptions: Optional[str] = None
    status: Status
    deadline: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "title": "Создать отчёт",
                "description": "Ежедневный отчёт по продажам",
                "status": "open",
                "deadline": "2026-02-10T18:00:00",
            }
        }


class TaskGet(BaseModel):
    id: int
    user_id: int
    title: str
    descriptions: Optional[str] = None
    status: Status
    deadline: datetime
