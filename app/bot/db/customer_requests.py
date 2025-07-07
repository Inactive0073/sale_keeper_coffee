from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy import select, update, func, case, and_
from sqlalchemy.dialects.postgresql import insert as upsert, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.bot.db.models import Customer, Bonus


logger = logging.getLogger(__name__)


async def upsert_customer(
    session: AsyncSession,
    telegram_id: int,
    first_name: str,
    last_name: str = None,
    username: str = None,
) -> None:
    """Создает или обновляет запись клиента в базе данных.

    Args:
        session: Асинхронная сессия SQLAlchemy
        telegram_id: Уникальный идентификатор пользователя в Telegram
        first_name: Имя пользователя
        last_name: Фамилия пользователя
        username: Юзернейм пользователя (без @)

    Example:
        await upsert_customer(session, 12345, 'john_doe', 'John', 'Doe')
    """
    values = {
        "telegram_id": telegram_id,
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }
    update_values = {
        "username": username,
        "first_name": first_name,
        "last_name": last_name,
    }
    stmt = upsert(Customer).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["telegram_id"],
        set_=dict(**update_values),
    )
    try:
        await session.execute(stmt)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        return False


async def get_all_customers(session: AsyncSession) -> list[int]:
    """Возвращает список Telegram-ID пользователей-клиентов.

    Args:
        session: Асинхронная сессия SQLAlchemy.

    Returns:
        List[int]: Список Telegram-ID пользователей.
    """
    stmt = select(Customer.telegram_id)
    result = await session.execute(stmt)
    return result.scalars().all()


async def record_personal_user_data(
    session: AsyncSession,
    telegram_id: int,
    name: str,
    surname: str,
    phone: str,
    email: str,
    birthday: str,
    gender: str,
) -> bool:
    """Добавляет персональные данные пользователя к его профилю в таблице и добавляет 100 приветственных бонусов к аккаунту"""
    values = {
        "i_name": name,
        "i_surname": surname,
        "phone": phone,
        "email": email,
        "birthday": birthday,
        "gender": gender,
    }
    user_stmt = (
        update(Customer).where(Customer.telegram_id == telegram_id).values(values)
    )
    bonus_stmt = upsert(Bonus).values(
        {"customer_id": telegram_id, "amount": 100, "source_type": "bonus"}
    )

    try:
        async with session.begin():
            user_result = await session.execute(user_stmt)
            await session.execute(bonus_stmt)
        return user_result.rowcount > 0

    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
        return False


async def get_bonus_info(
    session: AsyncSession, telegram_id: int
) -> tuple[int, datetime | None, int]:
    """Возвращает баланс бонусов пользователя

    Returns:
        Tuple[summary_bonus, date_expire, bonus_to_expire]:
            - summary_bonus: общий баланс бонусов
            - date_expire: ближайшая дата истечения баллов или None
            - bonus_to_expire: сумма баллов, истекающих в ближайшую дату
    """
    now = datetime.now(timezone.utc)
    min_expire_subquery = (
        select(func.coalesce(func.min(Bonus.expire_date), now + timedelta(weeks=52)))
        .where(
            and_(
                Bonus.customer_id == telegram_id,
                Bonus.expire_date > now,
                Bonus.amount != 0,
            )
        )
        .scalar_subquery()
    )
    stmt = select(
        func.sum(Bonus.amount).label("total_points"),
        min_expire_subquery.label("nearest_expiration_date"),
        func.sum(
            case((Bonus.expire_date == min_expire_subquery, Bonus.amount), else_=0)
        ).label("bonus_to_expire"),
    ).where(
        Bonus.customer_id == telegram_id,
        Bonus.expire_date > now,
        Bonus.amount != 0
    )

    result = await session.execute(stmt)
    row = result.one_or_none()

    if row:
        total_points, nearest_expiration_date, bonus_to_expire = row
        # Если nearest_expiration_date равна now + 52 недели, значит нет будущих истечений
        if nearest_expiration_date and nearest_expiration_date.date() == (now + timedelta(weeks=52)).date():
            nearest_expiration_date = None
        return (
            int(total_points or 0),
            nearest_expiration_date,
            int(bonus_to_expire or 0),
        )
    return None


async def get_customer_detail_info(
    session: AsyncSession, phone: str = None , telegram_id: int = None
) -> Customer:
    if phone is None and telegram_id is None:
        raise ValueError(f"Должен быть передан хотя бы один аргумент. Передано: {phone=}, {telegram_id=}")
    if phone:        
        stmt = select(Customer).where(Customer.phone == phone)
    else:
        stmt = select(Customer).where(Customer.telegram_id == telegram_id)
    result = await session.execute(stmt)
    customer = result.scalar_one_or_none()
    return customer


async def add_bonus(
    session: AsyncSession, customer_id: int, total_amount: int, expire_days: int = 365
) -> int:
    """
    Добавляет кэшбэк в таблицу Bonus и увеличивает счетчик визитов для клиента.

    Args:
        session: Асинхронная сессия SQLAlchemy.
        customer_id: Telegram ID клиента.
        total_amount: Сумма чека в условных единицах (например, рубли).
        expire_days: Количество дней до истечения кэшбэка (по умолчанию 365).
    """
    try:
        async with session.begin():
            stmt = select(Customer).where(Customer.telegram_id == customer_id)
            result = await session.execute(stmt)
            customer = result.scalar_one_or_none()

            if not customer:
                logger.error(f"Клиент с telegram_id {customer_id} не найден")
                return False

            cashback_amount = (total_amount * customer.percent_cashback) // 100

            # Вставляем новую запись о кэшбэке
            bonus_stmt = insert(Bonus).values(
                customer_id=customer_id,
                amount=cashback_amount,
                source_type="cashback",
                expire_date=datetime.now() + timedelta(days=expire_days),
            )

            # Обновляем счетчик визитов
            update_stmt = (
                update(Customer)
                .where(Customer.telegram_id == customer_id)
                .values(
                    visits=Customer.visits + 1,
                    visits_per_year=Customer.visits_per_year + 1,
                )
            )

            await session.execute(update_stmt)
            await session.execute(bonus_stmt)

        logger.info(
            f"Кэшбэк {cashback_amount} добавлен для клиента {customer_id}, визит обновлен"
        )
        return cashback_amount

    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {e}")
        return False


async def deduct_bonus(session: AsyncSession, customer_id: int, amount: int) -> int:
    """
    Списывает указанную сумму бонусов клиента, начиная с приближающихся горящих баллов.

    Args:
        session: Асинхронная сессия SQLAlchemy.
        customer_id: Telegram ID клиента.
        amount: Сумма бонусов в условных единицах.
    Returns:
        int: Фактическуи списанная сумма.
    """
    try:
        async with session.begin():
            stmt = (
                select(Bonus)
                .where(
                    Bonus.customer_id == customer_id,
                    Bonus.expire_date > func.now(),
                    Bonus.amount > 0,
                )
                .order_by(Bonus.expire_date.asc())
            )
            result = await session.execute(stmt)
            bonuses = result.scalars().all()

            remaining = amount
            for bonus in bonuses:
                if remaining <= 0:
                    break
                if bonus.amount >= remaining:
                    bonus.amount -= remaining
                    remaining = 0
                else:
                    remaining -= bonus.amount
                    bonus.amount = 0

            deducted = amount - remaining
            logger.info(f"Списано {deducted} бонусов для клиента {customer_id}")

            # Обновляем счетчик визитов
            update_stmt = (
                update(Customer)
                .where(Customer.telegram_id == customer_id)
                .values(
                    visits=Customer.visits + 1,
                    visits_per_year=Customer.visits_per_year + 1,
                )
            )
            await session.execute(update_stmt)

        return deducted
    except SQLAlchemyError as e:
        logger.error(f"Ошибка базы данных: {e}")
        return False
