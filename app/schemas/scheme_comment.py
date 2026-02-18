from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CommentGet(BaseModel):
    id: int
    written_at: datetime
    text: str
    user_id: UUID
    task_id: int

    model_config = ConfigDict(from_attributes=True)


class CommentCreate(BaseModel):
    text: str
    task_id: int

    class Config:
        json_schema_extra = {"example": {"text": "Any comment", "task_id": 1}}


class CommentUpdate(BaseModel):
    text: str
