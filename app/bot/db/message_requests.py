from typing import Literal
from sqlalchemy.dialects.postgresql import insert as upsert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update, func

from datetime import datetime
from .models.schedule_post import SchedulePost
from ..utils.enums import PostStatus, MessageType


# ------------------- Schedule Post Operations -------------------
async def upsert_post(
    session: AsyncSession,
    schedule_id: str,
    target_type: Literal["channel", "bot"],
    scheduled_time: datetime,
    data_json: dict,
    post_message: str,
    author_id: int,
) -> bool:
    """Создает или обновляет запись о запланированном посте в базе данных.

    Args:
        session: Асинхронная сессия SQLAlchemy
        schedule_id: Уникальный идентификатор запланированного поста
        target_type: Тип целевого объекта (канал или пользователь)
        scheduled_time: Время постинга
        data_json: Данные для отправки в формате JSON
        post_message: Сообщение поста
        author_id: Телеграм ID автора поста

    Example:
        await create_post(session, 1, "channel", datetime, {"key": "value"}, "Hello, world!", 12345)
    """
    values = {
        "schedule_id": schedule_id,
        "target_type": target_type,
        "scheduled_time": scheduled_time,
        "data_json": data_json,
        "post_message": post_message,
        "author_id": author_id,
    }
    update_values = {
        "target_type": target_type,
        "scheduled_time": scheduled_time,
        "data_json": data_json,
        "post_message": post_message,
    }
    stmt = (
        upsert(SchedulePost)
        .values(values)
        .on_conflict_do_update(
            index_elements=["schedule_id"], set_=dict(**update_values)
        )
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def get_post(
    session: AsyncSession,
    schedule_id: int,
) -> SchedulePost | None:
    """Получает запись о запланированном посте из базы данных по его ID."""
    result = await session.execute(
        select(SchedulePost).where(SchedulePost.schedule_id == schedule_id)
    )
    return result.scalar_one_or_none()


async def get_posts(
    session: AsyncSession, target_type: MessageType = None
) -> list[SchedulePost]:
    """Получить все запланированные посты"""
    stmt = select(SchedulePost).where(
        SchedulePost.scheduled_time > func.now(),
        SchedulePost.notify_status == PostStatus.SCHEDULED,
    )
    if target_type in MessageType:
        stmt = stmt.where(SchedulePost.target_type == target_type)
    result = await session.execute(stmt)
    return result.scalars().all()


async def delete_post(session: AsyncSession, schedule_id: str) -> bool:
    """Удаляет запись о запланированном посте из базы данных."""
    stmt = delete(SchedulePost).where(SchedulePost.schedule_id == schedule_id)
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0


async def cancel_post(session: AsyncSession, schedule_id: str) -> bool:
    """Удаляет запись о запланированном посте из базы данных."""
    stmt = (
        update(SchedulePost)
        .where(SchedulePost.schedule_id == schedule_id)
        .values(notify_status=PostStatus.CANCELED)
    )
    result = await session.execute(stmt)
    await session.commit()
    return result.rowcount > 0
