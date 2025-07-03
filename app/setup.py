import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties

from aiogram_dialog import setup_dialogs
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine,
    AsyncSession,
)

from dataclasses import dataclass

from aiogram.fsm.storage.base import DefaultKeyBuilder
from aiogram.enums import ParseMode

from taskiq_nats import NATSKeyValueScheduleSource


from .bot.db.base import Base
from .bot.middlewares import (
    DbSessionMiddleware,
    TrackAllUsersMiddleware,
    TranslatorRunnerMiddleware,
    ContextMiddleware,
)
from .bot.dialogs.setup import get_dialogs
from .bot.handlers.commands import commands_router
from .config_data.config import Config
from .storage.nats_storage import NatsStorage

logger = logging.getLogger(__name__)


@dataclass
class DependeciesConfig:
    config: Config

    async def setup_database(self) -> tuple[AsyncEngine, AsyncSession]:
        engine = create_async_engine(
            url=self.config.db.dsn, echo=self.config.db.is_echo
        )
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))  # Проверка соединения
            await conn.run_sync(Base.metadata.create_all)
        Sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        logger.info("Соединение к БД успешно проверено. ")
        return engine, Sessionmaker

    def setup_bot(self) -> Bot:
        bot = Bot(
            token=self.config.tg_bot.token,
            default=DefaultBotProperties(
                parse_mode=ParseMode.HTML, link_preview_is_disabled=True
            ),
        )
        self.bot = bot
        return bot

    async def setup_dispatcher(self, nc, js) -> Dispatcher:
        storage = await NatsStorage(
            nc=nc,
            js=js,
            key_builder=DefaultKeyBuilder(
                separator="_", with_destiny=True, with_bot_id=True
            ),
        ).create_storage()
        dp = Dispatcher(storage=storage)
        self.dp = dp
        return dp

    @staticmethod
    def register_middlewares_and_routers(
        dp: Dispatcher,
        Sessionmaker: AsyncSession,
        js,
        translator_hub,
        config: Config,
        nats_source: NATSKeyValueScheduleSource,
    ):
        # Регистриуем роутеры в диспетчере
        dp.include_router(commands_router)
        dp.include_routers(*get_dialogs())

        # Регистрируем миддлварь для i18n и бд
        dp.update.middleware(TranslatorRunnerMiddleware())
        dp.update.outer_middleware(DbSessionMiddleware(session_pool=Sessionmaker))
        dp.update.outer_middleware(
            ContextMiddleware(
                js=js,
                _translator_hub=translator_hub,
                web_app_url=config.tg_bot.url,
                nats_source=nats_source,
            )
        )
        dp.message.outer_middleware(TrackAllUsersMiddleware())

        # Запускаем функцию настройки проекта для работы с диалогами
        setup_dialogs(dp)

    @staticmethod
    async def set_commands(bot: Bot):
        commands = [BotCommand(command="/start", description="Запуск / Start")]
        await bot.set_my_commands(commands=commands)
