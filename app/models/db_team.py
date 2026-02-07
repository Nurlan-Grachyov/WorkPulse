from typing import Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.schemas.scheme_user import Role


class TeamUser(Base):  # Ассоциативная таблица
    __tablename__ = "team_users"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(
        SQLEnum(Role, name="team_role"), nullable=False, default=Role.USER
    )

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship(  # noqa:  F821
        "User", back_populates="team_links"
    )  # noqa:  F821


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)

    members: Mapped[Optional["TeamUser"]] = relationship(
        "TeamUser", back_populates="team", cascade="all, delete-orphan"
    )
