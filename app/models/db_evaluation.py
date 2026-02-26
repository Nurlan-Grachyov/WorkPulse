from sqlalchemy import ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    evaluation: Mapped[int] = mapped_column(Integer)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id"),
        unique=True,
        nullable=False,
    )

    task: Mapped["Task"] = relationship(  # noqa:  F821
        "Task",
        back_populates="evaluation",
    )
