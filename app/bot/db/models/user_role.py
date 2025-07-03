from sqlalchemy import BigInteger, SmallInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.bot.db import Base


class UserRole(Base):
    __tablename__ = "user_roles"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("users.telegram_id", ondelete="CASCADE"),
    )
    role_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("roles.role_id", ondelete="CASCADE")
    )
    __table_args__ = (UniqueConstraint("user_id", "role_id", name="unique_user_role"),)
