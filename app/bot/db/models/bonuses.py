from datetime import datetime, timedelta
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bot.db import Base
from app.bot.db.models.mixins import TimestampMixin


class Bonus(TimestampMixin, Base):
    __tablename__ = "bonuses"
    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, unique=True, autoincrement=True
    )
    customer_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("customers.telegram_id", ondelete="CASCADE")
    )
    amount: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    expire_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=func.now() + timedelta(days=365),
        server_default=func.now() + timedelta(days=365),
    )
    source_type: Mapped[str] = mapped_column(
        String, server_default=text("'cashback'"), default=text("'cashback'")
    )
    customer: Mapped["Customer"] = relationship(back_populates="bonuses")  # type: ignore
