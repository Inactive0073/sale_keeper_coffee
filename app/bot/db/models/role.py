from sqlalchemy import String, SmallInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.bot.db import Base
from app.bot.db.models.mixins import TimestampMixin


class Role(TimestampMixin, Base):
    __tablename__ = "roles"

    role_id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True)
    users: Mapped[list["User"]] = relationship(  # type: ignore
        secondary="user_roles", back_populates="roles", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"{self.name}"
