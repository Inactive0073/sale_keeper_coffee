from typing import Iterable

import logging

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from .models.user_role import UserRole
from .models.user import User
from ..utils.enums.role import UserType
from ..utils.exc import NotFoundError, AlreadyHaveAllRoles

from .common_requests import customer_exists

logger = logging.getLogger(__name__)


async def create_employee(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    role: UserType,
    username: str = None,
    last_name: str = None,
) -> bool:
    role_id = {UserType.WAITER: 1, UserType.MANAGER: 2, UserType.ADMIN: 3}.get(role)

    if role_id is None:
        logger.error(f"Неверная роль: {role}")
        return False

    # Проверка: существует ли пользователь в customers (запускал ли бот)
    if not await customer_exists(session=session, telegram_id=telegram_id):
        logger.error(
            f"Пользователь {telegram_id} не найден. Возможно, он не запускал бота."
        )
        raise NotFoundError

    # Обновление/добавление записи в таблице User
    stmt_upsert_user = (
        insert(User)
        .values(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        .on_conflict_do_update(
            index_elements=["telegram_id"],
            set_={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
            },
        )
    )
    await session.execute(stmt_upsert_user)

    # Проверка: есть ли у пользователя уже все роли
    stmt_current_roles = select(UserRole.role_id).where(UserRole.user_id == telegram_id)
    result = await session.execute(stmt_current_roles)
    current_roles = {row.role_id for row in result}

    all_roles = {1, 2, 3}
    if current_roles == all_roles:
        logger.info(f"Пользователь {telegram_id} уже имеет все роли.")
        raise AlreadyHaveAllRoles

    # Добавление новой роли, если ещё нет
    stmt_add_role = (
        insert(UserRole)
        .values(user_id=telegram_id, role_id=role_id)
        .on_conflict_do_nothing(index_elements=["user_id", "role_id"])
    )

    try:
        result = await session.execute(stmt_add_role)
        await session.commit()
        if result.rowcount > 0:
            logger.info(f"Добавлена роль {role} для пользователя {telegram_id}.")
            return True
        else:
            logger.info(f"Роль {role} уже была у пользователя {telegram_id}.")
            return False
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка при добавлении роли: {e}")
        return False


async def kick_employees(session: AsyncSession, telegram_ids: Iterable[int]) -> bool:
    """Удаляет роли у сотрудников по списку Telegram ID."""
    if not telegram_ids:
        logger.info("Передан пустой список telegram_ids, ничего не удалено.")
        return False

    stmt = delete(UserRole).where(UserRole.user_id.in_(telegram_ids))
    try:
        result = await session.execute(stmt)
        await session.commit()
        if result.rowcount > 0:
            logger.info(f"Удалены роли для сотрудников: {telegram_ids}")
            return True
        else:
            logger.info(f"Не найдены роли для удаления для сотрудников: {telegram_ids}")
            return False
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Ошибка при удалении ролей для сотрудников {telegram_ids}: {e}")
        return False


async def get_employee(session: AsyncSession, telegram_id: int) -> User:
    stmt = (
        select(User)
        .join(UserRole, UserRole.user_id == telegram_id)
        .where(User.telegram_id == telegram_id)
    )
    try:
        result = await session.execute(stmt)
        return result.one_or_none()
    except SQLAlchemyError as e:
        logger.error(
            f"Произошла ошибка при получении сотрудника {telegram_id}. Ошибка: {e}"
        )


async def get_employees(session: AsyncSession, size: int | None = None) -> list[User]:
    """Получает всех сотрудников с их ролями."""
    stmt = (
        select(User)
        .join(UserRole, UserRole.user_id == User.telegram_id)
        .distinct()
        .order_by(User.first_name)
    )
    if size is not None:
        stmt = stmt.limit(size)
    result = await session.execute(stmt)
    return result.scalars().all()
