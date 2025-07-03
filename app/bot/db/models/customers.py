from sqlalchemy import SmallInteger, String, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bot.db import Base
from app.bot.db.models.mixins import (
    TelegramProfileMixin,
    TimestampMixin,
    DetailProfileMixin,
)


class Customer(TimestampMixin, TelegramProfileMixin, DetailProfileMixin, Base):
    __tablename__ = "customers"
    gender: Mapped[str] = mapped_column(String(1), nullable=True)
    percent_cashback: Mapped[int] = mapped_column(
        SmallInteger, default=3, server_default=text("3")
    )
    visits_per_year: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default=text("0")
    )
    visits: Mapped[int] = mapped_column(
        SmallInteger, default=0, server_default=text("0")
    )
    bonuses: Mapped["Bonus"] = relationship(back_populates="customer")  # type: ignore
