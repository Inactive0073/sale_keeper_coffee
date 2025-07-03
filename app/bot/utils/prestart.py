from aiogram import Bot
from aiogram.types import BotCommand
from aiogram.methods.set_my_commands import SetMyCommands


async def setup_bot_commands(bot: Bot):
    # Список команд с описанием
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
    ]

    # Устанавливаем команды для бота
    await bot(SetMyCommands(commands=commands))
