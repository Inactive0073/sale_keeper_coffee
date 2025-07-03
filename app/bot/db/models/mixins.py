from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True, onupdate=datetime.now
    )


class TelegramProfileMixin:
    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, unique=True)
    phone: Mapped[str] = mapped_column(String(18), unique=True, nullable=True)
    first_name: Mapped[str]
    username: Mapped[str | None]
    last_name: Mapped[str | None]


class DetailProfileMixin:
    """Профиль для подробного описания пользователя с данными введеными вручную от пользователя"""

    i_name: Mapped[str | None]
    i_surname: Mapped[str | None]
    email: Mapped[str | None]
    birthday: Mapped[str | None] = mapped_column(String(10))
    gender: Mapped[str | None] = mapped_column(String(1))
