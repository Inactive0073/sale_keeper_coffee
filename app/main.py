import logging

from aiogram import Bot, Dispatcher
from aiogram.types import Update
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fluentogram import TranslatorHub

from .taskiq_broker.broker import broker, nats_source
from .config_data.config import Config, load_config

from .bot.utils import (
    create_translator_hub,
    connect_to_nats,
)
from .setup import DependeciesConfig


logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] #%(levelname)-8s %(filename)s:"
    "%(lineno)d - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


config: Config = load_config()
dependecies_config = DependeciesConfig(config)

bot: Bot
dp = Dispatcher(name="Taskiq_Dispatcher")  # Для taskiq
bot = dependecies_config.setup_bot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    global dp
    nc, js = await connect_to_nats(servers=config.nats.servers)  # Connect to NATS
    dp = await dependecies_config.setup_dispatcher(nc, js)  # Для бота
    await dependecies_config.set_commands(bot)
    translator_hub: TranslatorHub = create_translator_hub()
    engine, Sessionmaker = await dependecies_config.setup_database()

    await broker.startup()
    await nats_source.startup()

    dependecies_config.register_middlewares_and_routers(
        dp=dp,
        Sessionmaker=Sessionmaker,
        js=js,
        translator_hub=translator_hub,
        config=config,
        nats_source=nats_source,
    )

    webhook_url = config.get_webhook_url()
    await bot.set_webhook(
        url=webhook_url,
        allowed_updates=dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )
    logger.info(f"Webhook now on {webhook_url}")

    yield

    await nc.close()
    await bot.delete_webhook()
    await broker.shutdown()
    logger.info("Connection to NATS closed")


app = FastAPI(lifespan=lifespan)


@app.post("/bot")
async def webhook(request: Request) -> None:
    update = Update.model_validate(await request.json(), context={"bot": bot})
    await dp.feed_update(bot, update)


