from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import (
    BaseModel,
    ConfigDict,
    model_validator,
)


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

    # @field_validator("email")
    # @classmethod
    # def email_validator(cls, v):
    #     if "admin" in v or "manager" in v:
    #         raise ValueError("admin or manager cannot be used in email")


class UserRead(schemas.BaseUser[int]):
    # BaseUser already has email
    id: UUID
    slug: str
    role: Optional[RoleCompany] = None

    model_config = ConfigDict(from_attributes=True)


class UserReadWithTeamRole(BaseModel):
    # BaseUser already has email
    id: UUID
    slug: str
    team_role: Optional[RoleTeam] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    @classmethod
    def extract_team_role(cls, data):
        if hasattr(data, "team_link") and data.team_link:
            data.team_role = data.team_link.role
        else:
            data.team_role = RoleTeam.USER
        return data


class UserUpdate(schemas.BaseUserUpdate):
    role: Optional[RoleCompany] = None
