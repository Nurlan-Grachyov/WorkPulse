from datetime import datetime

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.database import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time: Mapped[datetime] = mapped_column(..., default=datetime.now, nullable=False)
    user_id: Mapped[int] = mapped_column(..., ForeignKey("users.id"), nullable=False)
    task_id: Mapped[int] = mapped_column(..., ForeignKey("tasks.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="comments")
    task: Mapped["Task"] = relationship("Task", back_populates="comments")
