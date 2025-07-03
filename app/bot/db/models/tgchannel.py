from sqlalchemy import BigInteger, String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bot.db.models.mixins import TimestampMixin
from app.bot.db import Base


class TgChannel(TimestampMixin, Base):
    __tablename__ = "channels"

    channel_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_name: Mapped[str] = mapped_column(String, nullable=False)
    channel_link: Mapped[str] = mapped_column(String, nullable=False)
    channel_username: Mapped[str] = mapped_column(String, nullable=False)
    channel_caption: Mapped[Text] = mapped_column(String, nullable=True)
    channel_auto_caption: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=True
    )
    # created_at добавляется из миксина

    # user: Mapped["User"] = relationship(back_populates="channels")  # type: ignore
    admins: Mapped[list["User"]] = relationship(  # type: ignore
        secondary="user_channels", back_populates="managed_channels", lazy="dynamic"
    )

    def __repr__(self) -> str:
        name = f"{self.channel_name} {self.channel_username}"
        return f"[{name} | {self.channel_id} | ссылка для вступления [{self.channel_link}]]"
