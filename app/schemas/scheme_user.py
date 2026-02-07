from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi_users import schemas


class Role(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class UserCreate(schemas.BaseUserCreate):
    # BaseUserCreate already has email and password
    role: Role = Role.USER

    class Config:
        json_schema_extra = {
            "example": {
                "email": "manager@example.com",
                "password": "strong_password_123",
            }
        }


class UserRead(schemas.BaseUser[int]):
    # BaseUser already has email
    id: UUID
    role: Optional[Role] = None


class UserUpdate(schemas.BaseUserUpdate):
    role: Optional[Role] = None
