from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

from app.schemas.scheme_team import TeamUserCreate


class Role(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: Optional[Role] = None
    team_links: Optional[TeamUserCreate] = None

    class Config:
        schema_extra = {
            "example": {
                "email": "manager@example.com",
                "hashed_password": "$2b$12$...",
                "role": None,
            }
        }

    @field_validator("role")
    @classmethod
    def role_must_be_admin_or_none(cls, v):
        if v is not None and v is not Role.ADMIN:
            raise ValueError("Роль может быть только admin или отсутствовать")
        return v


class UserGet(BaseModel):
    id: int
    email: EmailStr
    role: Optional[Role] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
