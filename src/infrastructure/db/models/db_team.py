from slugify import slugify
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.application.schemas.scheme_user import RoleTeam
from src.infrastructure.db.database import Base


class TeamUser(Base):  # Ассоциативная таблица
    __tablename__ = "team_users"

    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    role: Mapped[RoleTeam] = mapped_column(
        SQLEnum(RoleTeam, name="team_role"), nullable=False, default=RoleTeam.USER
    )  # локальная должность в команде

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship(  # noqa:  F821
        "User", back_populates="team_link"
    )  # noqa:  F821


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)

    members: Mapped[list["TeamUser"]] = relationship(
        "TeamUser", back_populates="team", cascade="all, delete-orphan"
    )
    tasks: Mapped[list["Task"]] = relationship(  # noqa:  F821
        "Task", back_populates="team", cascade="all, delete-orphan"
    )


@event.listens_for(Team, "before_insert")
def set_team_slug(mapper, connection, target):
    if not target.slug and target.title:
        target.slug = slugify(target.title)
