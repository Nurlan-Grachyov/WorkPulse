from datetime import datetime

from pydantic import BaseModel


class CommentGet(BaseModel):
    id: int
    written_at: datetime
    user_id: int
    task_id: int


class CommentCreate(BaseModel):
    user_id: int
    task_id: int

    class Config:
        json_schema_extra = {"example": {"user_id": 1, "task_id": 1}}
