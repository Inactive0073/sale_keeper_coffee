import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery

from typing import TYPE_CHECKING

from aiogram_dialog import DialogManager, ShowMode, ChatEvent
from aiogram_dialog.widgets.kbd import Button, ManagedCheckbox
from aiogram_dialog.widgets.input import TextInput
from fluentogram import TranslatorRunner
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.db.manager_requests import (
    delete_caption_channel,
    delete_channel,
    toggle_auto_caption_channel,
    upsert_caption_channel,
    upsert_channel_with_admin,
)
from app.bot.states.manager.addition_channel import AdditionToChannelSG

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type: ignore

logger = logging.getLogger(__name__)


def validate_channel(text: str):
    """Проверяет корректность формата ввода для username или ссылки на канал.

    Возвращает очищенный username канала. Вызывает ValueError при неверном формате.
    """
    logger.debug(f"Начата валидация введенного канала: {text}")
    channel_name = text.startswith("@")
    link = text.find("https://t.me/")
    if not channel_name and link == -1:
        logger.error(f"Некорректный формат канала: {text}")
        raise ValueError

    if link == -1:
        return text
    else:
        cleaned = text[text.find("@") :]
        logger.debug(f"Очищенный username канала: {cleaned}")
        return cleaned


async def on_invalid_channel(
    message: Message, widget: TextInput, dialog_manager: DialogManager, err: ValueError
):
    """Отправляет сообщение о неверном формате канала и удаляет исходное сообщение."""
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    dialog_manager.show_mode = ShowMode.DELETE_AND_SEND
    user_id = message.from_user.id
    logger.warning(
        f"Пользователь {user_id} ввел некорректный формат канала: {message.text}"
    )
    await message.answer(i18n.channel.link.invalid())
    await message.delete()


async def check_admin_status(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    text: str,
):
    """Основной хэндлер для проверки прав бота и сохранения канала в БД."""
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    user_id = message.from_user.id
    logger.info(
        f"Начата проверка прав для канала {text} пользователем {message.from_user.username}|{user_id}"
    )

    try:
        chat_full_info = await bot.get_chat(chat_id=text)
        logger.debug(f"Получена информация о канале: {chat_full_info}")
    except TelegramBadRequest as e:
        logger.error(f"Ошибка при получении информации о канале {text}: {e}")
        await message.answer(i18n.channel.link.invalid())
        return

    if chat_full_info.type in ("private", "group", "supergroup"):
        logger.warning(f"Неподходящий тип чата {chat_full_info.type} для канала {text}")
        await message.answer(i18n.channel.link.wrong.type())
        return

    try:
        await upsert_channel_with_admin(
            session=session,
            channel_id=chat_full_info.id,
            channel_name=chat_full_info.title,
            channel_username=chat_full_info.username,
            channel_link=chat_full_info.invite_link,
            admin_id=user_id,
        )
        logger.info(f"Канал {chat_full_info.id} успешно сохранен в БД")
    except Exception as e:
        logger.critical(f"Ошибка при сохранении канала {chat_full_info.id} в БД: {e}")
        await message.answer(i18n.error())
        return

    await message.answer(i18n.channel.link.after.joining.channel())
    await message.delete()
    logger.info(f"Канал {text} успешно добавлен пользователем {user_id}")


async def on_channel_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager, item_id: str
):
    channel_id = int(item_id)
    logger.info(f"Пользователь {callback.from_user.id} выбрал канал ID: {channel_id}")
    dialog_manager.dialog_data["channel_selected_id"] = channel_id
    await dialog_manager.switch_to(
        state=AdditionToChannelSG.channel_settings, show_mode=ShowMode.DELETE_AND_SEND
    )


async def delete_channel_from_bot(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
):
    """Хендлер для удаления канала из бота"""
    channel_id = dialog_manager.dialog_data["channel_selected_id"]
    bot: Bot = dialog_manager.middleware_data.get("bot")
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    user_id = callback.from_user.id

    logger.info(f"Начато удаление канала {channel_id} пользователем {user_id}")

    try:
        result = await bot.leave_chat(channel_id)
        if result:
            await delete_channel(session=session, channel_id=channel_id)
            logger.info(f"Канал {channel_id} успешно удален")
            await callback.answer(i18n.channel.success.deleted())
        else:
            logger.error(f"Не удалось покинуть канал {channel_id}")
            await callback.answer(i18n.channel.unsuccessful.deleted())
    except Exception as e:
        logger.critical(f"Ошибка при удалении канала {channel_id}: {e}")
        await callback.answer(i18n.error())


async def delete_caption(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
):
    """Хендлер для удаления подписи из канала пользователя"""
    channel_id = dialog_manager.dialog_data["channel_selected_id"]
    bot: Bot = dialog_manager.middleware_data.get("bot")
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session: AsyncSession = dialog_manager.middleware_data.get("session")
    user_id = callback.from_user.id
    username = callback.from_user.username
    result = await delete_caption_channel(session=session, channel_id=channel_id)
    if result:
        logger.info(f"{username}|{user_id} успешно удалил подпись к каналу")
    else:
        logger.error(
            f"Возникла ошибка {username}|{user_id} не смог удалить подпись к каналу {channel_id}"
        )


async def add_caption_to_channel(
    message: Message, widget: TextInput, dialog_manager: DialogManager, text: str
):
    """Хендлер для добавления автоподписи к боту"""
    session = dialog_manager.middleware_data.get("session")

    channel_id = dialog_manager.dialog_data.get("channel_selected_id")
    await upsert_caption_channel(session=session, channel_id=channel_id, caption=text)
    logger.info(f"Для канала {channel_id}, добавлена автоподпись: [{text}]")
    await message.delete()
    await dialog_manager.switch_to(state=AdditionToChannelSG.channel_settings)


async def auto_caption_changed(
    event: ChatEvent, checkbox: ManagedCheckbox, dialog_manager: DialogManager
):
    session = dialog_manager.middleware_data.get("session")
    channel_id = dialog_manager.dialog_data.get("channel_selected_id")
    username = event.from_user.username
    user_id = event.from_user.id

    is_checked = checkbox.is_checked()
    result = await toggle_auto_caption_channel(
        session=session,
        channel_id=channel_id,
        option=is_checked,
    )
    if result:
        logger.info(
            f"{username}|{user_id} {'включил' if is_checked else 'выключил'} автоподпись."
        )
    else:
        logger.error(
            f"Произошла ошибка во время переключения автоподписи юзером {username}|{user_id}"
            f"с состояния {'включил' if is_checked else 'выключил'}"
        )


async def handle_error_caption(
    message: Message, widget: TextInput, dialog_manager: DialogManager, err: ValueError
):
    """Обрабатывает некорректний тип присланного сообщения."""
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    await message.answer(i18n.channel.caption.error())
    await message.delete()
