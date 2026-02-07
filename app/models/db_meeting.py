from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(20), nullable=False)
    starts_at: Mapped[datetime] = mapped_column(default=datetime.now, nullable=False)

    users: Mapped[list["User"]] = relationship(  # noqa:  F821
        "User", secondary="meeting_participants", back_populates="meetings"
    )


meeting_participants = Table(
    "meeting_participants",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("meeting_id", ForeignKey("meetings.id"), primary_key=True),
)
