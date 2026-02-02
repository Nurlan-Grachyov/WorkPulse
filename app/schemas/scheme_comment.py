from datetime import datetime

from pydantic import BaseModel


class CommentGet(BaseModel):
    id: int
    written_at: datetime
    user_id: int
    task_id: int


class CommentCreate(BaseModel):
    written_at: datetime
    user_id: int
    task_id: int
