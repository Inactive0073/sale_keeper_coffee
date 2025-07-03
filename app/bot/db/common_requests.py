from typing import Type, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.db.models import Role, UserRole, User, Customer


async def get_user_role(session: AsyncSession, telegram_id: int) -> list[str]:
    "Возвращает список ролей пользователя"
    stmt = (
        select(Role.name)
        .join(UserRole, Role.role_id == UserRole.role_id)
        .where(UserRole.user_id == telegram_id)
    )
    result = await session.execute(stmt)
    return result.scalars().all()


async def get_telegram_id_by_username(
    session: AsyncSession,
    username: str,
    target: Type[Union[Customer, User]] = User,
) -> int | None:
    "Возвращает Telegram ID по никнейму пользователя."
    stmt = select(target.telegram_id).where(target.username == username)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def customer_exists(session: AsyncSession, telegram_id: int) -> bool:
    stmt = select(Customer).where(Customer.telegram_id == telegram_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none() is not None
