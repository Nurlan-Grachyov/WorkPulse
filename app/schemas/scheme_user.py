from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import ConfigDict, field_validator


class RoleCompany(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class RoleTeam(str, Enum):
    USER = "user"
    MANAGER = "manager"


class UserCreate(schemas.BaseUserCreate):
    # BaseUserCreate already has email and password

    class Config:
        json_schema_extra = {
            "example": {
                "email": "manager@example.com",
                "password": "strong_password_123",
            }
        }

    @field_validator("email")
    @classmethod
    def email_validator(cls, v):
        if "admin" in v or "manager" in v:
            raise ValueError("admin or manager cannot be used in email")


class UserRead(schemas.BaseUser[int]):
    # BaseUser already has email
    id: UUID
    slug: str
    role: Optional[RoleCompany] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(schemas.BaseUserUpdate):
    role: Optional[RoleCompany] = None
