from typing import Optional
from uuid import uuid4

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from slugify import slugify
from sqlalchemy import UUID, Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.application.schemas.scheme_user import RoleCompany
from src.infrastructure.db.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[RoleCompany] = mapped_column(
        SQLEnum(RoleCompany, name="user_role"), nullable=False, default=RoleCompany.USER
    )  # глобальная должность в компании
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    comments: Mapped[list["Comment"]] = relationship(  # noqa:  F821
        "Comment",
        back_populates="user",
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa:  F821
        "Task",
        back_populates="assignee",
        cascade="all, delete-orphan",
    )
    meetings: Mapped[list["Meeting"]] = relationship(  # noqa:  F821
        "Meeting", secondary="meeting_participants", back_populates="users"
    )
    team_link: Mapped[Optional["TeamUser"]] = relationship(  # noqa:  F821
        "TeamUser", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


@event.listens_for(User, "before_insert")
def set_user_slug(mapper, connection, target):
    if not target.slug:
        target.slug = slugify(target.email.split("@")[0].replace(".", "-").lower())
