from typing import Optional
from slugify import slugify

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from sqlalchemy import Boolean, event
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.schemas.scheme_user import Role


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="user_role"), nullable=False, default=Role.USER
    )
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True)

    comments: Mapped[list["Comment"]] = relationship(  # noqa:  F821
        "Comment",
        back_populates="user",
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa:  F821
        "Task",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    meetings: Mapped[list["Meeting"]] = relationship(  # noqa:  F821
        "Meeting", secondary="meeting_participants", back_populates="users"
    )
    team_links: Mapped[Optional["TeamUser"]] = relationship(  # noqa:  F821
        "TeamUser", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    @hybrid_property
    def username_slug(self) -> str:
        return self.email.split("@")[0].replace(".", "-")

@event.listens_for(User, "before_insert")
@event.listens_for(User, "before_update")
def set_user_slug(mapper, connection, target):
    if not target.slug:
        target.slug = slugify(target.email.split("@")[0].replace(".", "-"))
