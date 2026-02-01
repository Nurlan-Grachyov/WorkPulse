from datetime import datetime
from enum import Enum

from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SQLEnum

from app.database import Base


class Status(str, Enum):
    OPEN = "open"
    IN_PROCESS = "in process"
    DONE = "done"


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[Integer] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[Status] = mapped_column(
        SQLEnum(Status, name="task_status"), default=Status.OPEN
    )  # open, in process, done
    deadline: Mapped[datetime] = mapped_column(DateTime)

    comments: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="task",
        cascade="all, delete-orphan",
    )
    user: Mapped["User"] = relationship("User", back_populates="tasks")
