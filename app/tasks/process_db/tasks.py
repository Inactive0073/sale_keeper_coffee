import logging
from datetime import datetime, timezone

import clickhouse_connect
import asyncpg

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import case, delete, and_, or_, update, select
from sqlalchemy.exc import SQLAlchemyError

from app.bot.db.models.customers import Customer
from app.config_data.config import Config, load_config
from app.bot.db.models.bonuses import Bonus
from app.taskiq_broker.broker import broker

logger = logging.getLogger(__name__)
config: Config = load_config()
engine = create_async_engine(url=config.db.dsn, echo=config.db.is_echo)


@broker.task(task_name="insert_from_psql_to_clickhouse", schedule=[{"cron": "5 * * * *"}])
async def insert_from_psql_to_clickhouse():
    """Тестовая функция для MRE примера"""
    client = clickhouse_connect.get_client(
        host=config.clickhouse.host,
        username=config.clickhouse.username,
        password=config.clickhouse.password,
        database=config.clickhouse.db,
        port=config.clickhouse.port
    )

    # Забираем последний id-шник, чтобы фильтровать сдвиг продаж по нему
    last_id = client.query("SELECT max(last_sale_id) FROM date_offsets").first_item or 0
    logger.info(f"Последний {last_id=} для выборки")

    conn: asyncpg.Connection = await asyncpg.connect(
        host="coffee_postgres",
        port=5433,
        user=config.clickhouse.username,
        password=config.clickhouse.password,
        database="db_in_psg"
    )
    sales_rows: list[asyncpg.Record] = await conn.fetch("""
        SELECT id, store_id, sale_date, product_category, product_name, quantity, price
        FROM sales
        WHERE id > $1
        ORDER BY id ASC
    """, last_id)
    await conn.close()
    
    if not sales_rows:
        return "Нет новых данных"
    

    data = [tuple(r.values()) for r in sales_rows]

    # Вставка данных в клик
    client.insert(
        "local_sales",
        data,
        column_names=["id", "store_id", "sale_date", "product_category", "product_name", "quantity", "price"]
    )
    
    # Обновление offset
    last_id_offset = data[-1][0]
    client.insert(
        table="date_offsets",
        data=[(1, last_id_offset)],
        column_names=["offset_id", "last_sale_id"]
    )


@broker.task(
    task_name="delete_old_or_empty_bonus", schedule=[{"cron": "0 4 * * *"}]
)  # запуск ежедневно в 4:00
async def delete_empty_bonus():
    async with AsyncSession(engine) as session:
        try:
            current_time = datetime.now(timezone.utc)
            stmt = delete(Bonus).where(
                and_(or_(Bonus.amount == 0, Bonus.expire_date < current_time))
            )
            result = await session.execute(stmt)
            logger.info(f"Удалено {result.rowcount} записей из таблицы бонусов.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при удалении записей бонусов: {e}")


@broker.task(
    task_name="upgrade_bonus_level", schedule=[{"cron": "10 4 * * *"}]
)  # запуск ежедневно в 4:10
async def upgrade_bonus_level():
    async with AsyncSession(engine) as session:
        try:
            update_stmt = update(Customer).values(
                percent_cashback=case(
                    {
                        (Customer.visits >= 80): case(
                            {
                                (Customer.visits_per_year >= 20): 10,
                                (Customer.visits_per_year < 20): 7,
                            }
                        ),
                        (Customer.visits >= 60): 7,
                        (Customer.visits >= 30): 5,
                    },
                    else_=3,
                )
            )
            await session.execute(update_stmt)
            await session.commit()
            logger.info("Обновлены уровни кэшбэка для всех клиентов.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Произошла ошибка при обновлении уровней кэшбэка: {e}")


@broker.task(
    task_name="reset_visits_per_year", schedule=[{"cron": "0 0 1 1 *"}]
)  # Запускается 1 января в 00:00 UTC
async def reset_visits_per_year():
    async with AsyncSession(engine) as session:
        try:
            update_stmt = update(Customer).values(visits_per_year=0)
            await session.execute(update_stmt)
            await session.commit()
            logger.info("Ежегодный счетчик визитов обнулен для всех клиентов.")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при обнулении ежегодного счетчика визитов: {e}")
