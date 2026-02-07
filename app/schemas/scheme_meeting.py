from datetime import datetime

from pydantic import BaseModel


class MeetingCreate(BaseModel):
    title: str
    starts_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "title": "the first meeting",
                "starts_at": "2026-02-10T18:00:00",
            }
        }


class MeetingGet(BaseModel):
    id: int
    title: str
    starts_at: datetime
