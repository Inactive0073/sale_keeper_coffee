"""
Модуль для работы с базой данных Telegram-бота.

Содержит CRUD-операции для моделей User и TgChannel с использованием SQLAlchemy AsyncSession.
Поддерживает PostgreSQL-специфичные UPSERT-операции через on_conflict_do_update.
"""

from typing import cast, Literal
from sqlalchemy import select, delete, update
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.ext.asyncio import AsyncSession
from app.bot.db.models import TgChannel, User, UserChannel


async def get_user_tz(
    session: AsyncSession,
    telegram_id: int,
) -> tuple[str, int]:
    """Возвращает часовой пояс пользователя. По умолчанию у всех пользователей выставлен Europe/Moscow, offset=3"""
    stmt = select(User.timezone, User.timezone_offset).where(
        User.telegram_id == telegram_id
    )
    result = await session.execute(stmt)
    tz, tz_offset = result.first()
    return tz, tz_offset


async def set_user_tz(
    session: AsyncSession, telegram_id: int, tz_offset: int, timezone: str
) -> bool:
    """Устанавливает часовой пояс пользователя.
    По умолчанию у всех пользователей выставлен Europe/Moscow"""
    stmt = (
        update(User)
        .where(User.telegram_id == telegram_id)
        .values(timezone=timezone, timezone_offset=tz_offset)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def get_users(
    session: AsyncSession,
    number_of_users: int,
) -> list[User]:
    """Возвращает список пользователей с сортировкой по имени.

    Args:
        session: Асинхронная сессия SQLAlchemy
        number_of_users: Максимальное количество возвращаемых пользователей

    Returns:
        Список объектов User, отсортированных по first_name

    Example:
        users = await get_users(session, 10)
    """
    stmt = select(User).order_by(User.first_name).limit(number_of_users)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return cast(list[User], users)


# ------------------- Channel Operations -------------------


async def upsert_channel(
    session: AsyncSession,
    channel_id: int,
    channel_name: str,
    channel_username: str,
    channel_link: str,
) -> None:
    """Создает или обновляет запись Telegram-канала.

    Args:
        session: Асинхронная сессия SQLAlchemy
        channel_id: Уникальный ID канала
        channel_name: Название канала
        channel_username: Юзернейм канала (без @)
        channel_link: Пригласительная ссылка

    Example:
        await upsert_channel(session, -100123, 'My Channel', 'mychannel', 'https://t.me/mychannel')
    """
    stmt = (
        upsert(TgChannel)
        .values(
            {
                "channel_id": channel_id,
                "channel_name": channel_name,
                "channel_username": channel_username,
                "channel_link": channel_link,
            }
        )
        .on_conflict_do_update(
            index_elements=["channel_id"],
            set_=dict(channel_name=channel_name, channel_link=channel_link),
        )
    )
    await session.execute(stmt)
    await session.commit()


async def get_channels(
    session: AsyncSession, telegram_id: int
) -> list[Literal["telegram_id", "channel_name", "channel_username", "channel_link"]]:
    """Возвращает каналы, принадлежащие указанному администратору.

    Args:
        session: Асинхронная сессия SQLAlchemy
        telegram_id: ID пользователя-администратора

    Returns:
        Список кортежей с данными каналов в формате:
        (channel_id, name, username, link)

    Example:
        channels = await get_channels(session, 12345)
    """
    stmt = (
        select(TgChannel)
        .join(UserChannel, TgChannel.channel_id == UserChannel.channel_id)
        .where(UserChannel.user_id == telegram_id)
    )
    result = await session.execute(stmt)
    return [
        (
            channel.channel_id,
            channel.channel_name,
            channel.channel_username,
            channel.channel_link,
        )
        for channel in result.scalars()
    ]


async def get_channel(session: AsyncSession, channel_id: int) -> TgChannel:
    """Возвращает канал по его ID.

    Args:
        session: Асинхронная сессия SQLAlchemy
        channel_id: ID целевого канала

    Returns:
        Объект TgChannel или None, если канал не найден

    Example:
        channel = await get_channel(session, -100123)
    """
    print(f"{channel_id=}")
    stmt = select(TgChannel).where(TgChannel.channel_id == channel_id)
    result = await session.execute(stmt)
    return result.scalars().first()


async def delete_channel(session: AsyncSession, channel_id: int) -> bool:
    """Удаляет канал из базы данных.

    Args:
        session: Асинхронная сессия SQLAlchemy
        channel_id: ID канала для удаления

    Returns:
        True если канал был удален, False если канал не найден

    Example:
        success = await delete_channel(session, -100123)
    """
    stmt = delete(TgChannel).where(TgChannel.channel_id == channel_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


# ------------------- Channel-Admin Relationship -------------------
async def add_admin_to_channel(
    session: AsyncSession,
    user_id: int,
    channel_id: int,
) -> None:
    """Добавляет админа к каналу"""
    stmt = upsert(UserChannel).values(user_id=user_id, channel_id=channel_id)
    await session.execute(stmt)
    await session.commit()


async def remove_admin_from_channel(
    session: AsyncSession,
    user_id: int,
    channel_id: int,
) -> None:
    """Удаляет админа из канала"""
    stmt = delete(UserChannel).where(
        (UserChannel.user_id == user_id, UserChannel.channel_id == channel_id)
    )
    await session.execute(stmt)
    await session.commit()


# ------------------- Advanced Helpers -------------------
async def upsert_channel_with_admin(
    session: AsyncSession,
    channel_id: int,
    channel_name: str,
    channel_username: str,
    channel_link: str,
    admin_id: int,
) -> None:
    """Создает канал и сразу назначает администратора"""
    await upsert_channel(
        session, channel_id, channel_name, channel_username, channel_link
    )
    await add_admin_to_channel(session, admin_id, channel_id)


# ------------------- Caption Operations -------------------
async def upsert_caption_channel(
    session: AsyncSession, channel_id: int, caption: str
) -> None:
    """Обновляет подпись для существующего канала.

    Args:
        session: Асинхронная сессия SQLAlchemy
        channel_id: ID целевого канала
        caption: Новая подпись для канала

    Example:
        await upsert_caption_channel(session, -100123, "New channel description")
    """
    stmt = (
        update(TgChannel)
        .where(TgChannel.channel_id == channel_id)
        .values(channel_caption=caption)
    )
    result = await session.execute(stmt)
    await session.commit()


async def get_caption_channel(session: AsyncSession, channel_id: int) -> str:
    """Возвращает подпись канала к посту"""
    stmt = select(TgChannel.channel_caption).where(TgChannel.channel_id == channel_id)
    result = await session.execute(stmt)
    caption = result.first()[0]
    return caption


async def delete_caption_channel(session: AsyncSession, channel_id: int) -> bool:
    """Удаляет подпись к посту"""
    stmt = (
        update(TgChannel)
        .where(TgChannel.channel_id == channel_id)
        .values(channel_caption=None)
    )
    result = await session.execute(stmt)
    await session.commit()
    if result:
        return True


async def toggle_auto_caption_channel(
    session: AsyncSession, channel_id: int, option: bool
) -> bool:
    """Переключает автоподпись канала"""
    stmt = (
        update(TgChannel)
        .where(TgChannel.channel_id == channel_id)
        .values(channel_auto_caption=option)
    )
    result = await session.execute(stmt)
    await session.commit()
    if result:
        return True
