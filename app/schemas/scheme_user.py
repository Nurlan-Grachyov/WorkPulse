from enum import Enum
from typing import Optional
from uuid import UUID

from fastapi_users import schemas
from pydantic import ConfigDict, field_validator, BaseModel, EmailStr


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


class TeamMemberUser(BaseModel):
    slug: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class TeamMemberLink(BaseModel):
    role: RoleTeam
    user: TeamMemberUser  # участник команды

    model_config = ConfigDict(from_attributes=True)


class TeamShort(BaseModel):
    slug: str
    title: str
    members: list[TeamMemberLink]

    model_config = ConfigDict(from_attributes=True)


class TeamLinkRead(BaseModel):
    role: RoleTeam
    team: TeamShort

    model_config = ConfigDict(from_attributes=True)


class UserReadWithTeamLink(BaseModel):
    slug: str
    email: EmailStr
    is_active: bool
    role: RoleCompany
    team_link: TeamLinkRead | None

    model_config = ConfigDict(from_attributes=True)