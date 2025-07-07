from dataclasses import dataclass
from environs import Env

from typing import List


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    url: str  # URL для вебхука


@dataclass
class NatsConfig:
    servers: List[str]


@dataclass
class DataBase:
    dsn: str
    is_echo: bool


@dataclass
class Config:
    tg_bot: TgBot
    nats: NatsConfig
    db: DataBase

    def get_webhook_url(self) -> str:
        return f"{self.tg_bot.url}/bot"


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path, override=True)
    return Config(
        tg_bot=TgBot(token=env("BOT_TOKEN"), url=env("BOT_WEBHOOK_URL")),
        nats=NatsConfig(servers=env.list("NATS_SERVERS")),
        db=DataBase(dsn=env("DSN"), is_echo=env.bool(("IS_ECHO"))),
    )
