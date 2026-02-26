from datetime import datetime
from enum import Enum

from slugify import slugify
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Integer, String, event
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Status(str, Enum):
    OPEN = "open"
    IN_PROCESS = "in process"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignee_id: Mapped[Integer] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[Status] = mapped_column(
        SQLEnum(Status, name="task_status"), default=Status.OPEN
    )  # open, in process, done
    deadline: Mapped[datetime] = mapped_column(DateTime)
    team_id: Mapped[int] = mapped_column(ForeignKey("teams.id"), nullable=False)

    comments: Mapped[list["Comment"]] = relationship(  # noqa:  F821
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    assignee: Mapped["User"] = relationship(  # noqa:  F821
        "User", back_populates="tasks"
    )
    team: Mapped["Team"] = relationship("Team", back_populates="tasks")  # noqa:  F821
    evaluation: Mapped["Evaluation"] = relationship(  # noqa:  F821
        "Evaluation",
        back_populates="task",
        uselist=False,
        cascade="all, delete-orphan",
    )


@event.listens_for(Task, "before_insert")
def set_team_slug(mapper, connection, target):
    if not target.slug and target.title:
        target.slug = slugify(target.title)
