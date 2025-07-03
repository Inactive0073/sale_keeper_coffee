from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.bot.db import Base


class UserChannel(Base):
    __tablename__ = "user_channels"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
    )
    channel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("channels.channel_id", ondelete="CASCADE")
    )
