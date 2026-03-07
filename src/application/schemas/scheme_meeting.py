from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class MeetingCreate(BaseModel):
    title: str
    starts_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "title": "the first meeting",
                "starts_at": "2026-02-10 18:00:00",
            }
        }
    )

    @field_validator("starts_at", mode="before")
    @classmethod
    def parse_human_datetime(cls, v):
        if isinstance(v, datetime):
            return v

        if isinstance(v, str):
            try:
                # поддерживаем формат "YYYY-MM-DD HH:MM:SS"
                return datetime.strptime(v, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                raise ValueError(
                    "Invalid datetime format, expected 'YYYY-MM-DD HH:MM:SS'"
                )
        return v

    @field_validator("starts_at", mode="after")
    @classmethod
    def check_date(cls, v):
        if v < datetime.now():
            raise ValueError("Can not create a meeting with past date")
        return v


class MeetingGet(BaseModel):
    id: int
    title: str
    starts_at: datetime

    model_config = ConfigDict(from_attributes=True)
