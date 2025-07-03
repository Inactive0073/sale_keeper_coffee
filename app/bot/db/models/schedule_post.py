from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, Text, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from typing import Optional

from app.bot.db.models.mixins import TimestampMixin
from app.bot.db import Base

from app.bot.utils.enums import PostStatus


class SchedulePost(TimestampMixin, Base):
    __tablename__ = "schedule_posts"

    schedule_id: Mapped[str] = mapped_column(Text, primary_key=True, unique=True)
    target_type: Mapped[str]
    scheduled_time: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    data_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    post_message: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE")
    )
    notify_status: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        server_default=PostStatus.SCHEDULED,
        default=PostStatus.SCHEDULED,
    )
    user: Mapped["User"] = relationship(back_populates="schedule_posts")  # type: ignore
