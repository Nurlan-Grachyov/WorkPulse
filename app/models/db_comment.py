from datetime import datetime

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    written_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)

    user: Mapped["User"] = relationship(  # noqa:  F821
        "User", back_populates="comments"
    )  # noqa:  F821
    task: Mapped["Task"] = relationship(  # noqa:  F821
        "Task", back_populates="comments"
    )  # noqa:  F821
