from enum import Enum

from pydantic import BaseModel


class Role(str, Enum):
    USER = "user"
    MANAGER = "manager"
    ADMIN = "admin"


class TeamUserCreate(BaseModel):
    team_id: int
    user_id: int
    role: Role


class TeamCreate(BaseModel):
    title: str

    class Config:
        scheme_extra = {
            "example": {
                "title": "Create employer's system",
            }
        }


class TeamGet(BaseModel):
    id: int
    title: str
