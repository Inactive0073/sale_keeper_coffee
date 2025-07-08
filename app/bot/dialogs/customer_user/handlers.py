from datetime import datetime
import logging
from aiogram import Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
)
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import MessageInput, ManagedTextInput

from fluentogram import TranslatorRunner

from typing import TYPE_CHECKING

from app.bot.states.customer.start import CustomerSG
from app.bot.db.customer_requests import (
    get_bonus_info,
    record_personal_user_data,
    get_customer_detail_info,
)
from .keyboards import get_kb
from .services import convert_media_to_group, normalize_phone_number

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type: ignore


logger = logging.getLogger(__name__)


async def process_succes_contact(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager,
):
    """Обрабатывает отправленный контакт и формирует диалог дату для дальнейшего сохранения в БД"""
    dialog_manager.dialog_data["phone"] = message.contact.phone_number
    await message.delete()
    await dialog_manager.switch_to(
        state=CustomerSG.name, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_invalid_phone(
    message: Message,
    message_input: MessageInput,
    dialog_manager: DialogManager,
):
    """Обрабатывает неправильный ввод данных"""
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    await message.delete()
    await message.answer(i18n.customer.error.phone())


async def process_succes_name(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    await message.delete()
    dialog_manager.dialog_data["name"] = text
    await dialog_manager.switch_to(
        state=CustomerSG.surname, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_succes_surname(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    await message.delete()
    dialog_manager.dialog_data["surname"] = text
    await dialog_manager.switch_to(
        state=CustomerSG.email, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_succes_email(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    await message.delete()
    dialog_manager.dialog_data["email"] = text
    await dialog_manager.switch_to(
        state=CustomerSG.birthday, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_succes_birthday(
    message: Message, widget: ManagedTextInput, dialog_manager: DialogManager, text: str
):
    await message.delete()
    dialog_manager.dialog_data["birthday"] = text
    await dialog_manager.switch_to(
        state=CustomerSG.gender, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_invalid_birthday(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError,
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    await message.answer(i18n.customer.error.birthday())
    await message.delete()


async def process_gender_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session = dialog_manager.middleware_data.get("session")
    dialog_manager.dialog_data["gender"] = callback.data
    await callback.message.answer(i18n.customer.meeting.thanks())

    # Сохранение введеных данных в БД
    telegram_id = callback.from_user.id
    name = dialog_manager.dialog_data.get("name")
    surname = dialog_manager.dialog_data.get("surname")
    phone = normalize_phone_number(dialog_manager.dialog_data.get("phone"))
    email = dialog_manager.dialog_data.get("email")
    birthday = dialog_manager.dialog_data.get("birthday")
    gender = dialog_manager.dialog_data.get("gender", "N")[0]

    if await record_personal_user_data(
        session=session,
        telegram_id=telegram_id,
        name=name,
        surname=surname,
        phone=phone,
        email=email,
        birthday=birthday,
        gender=gender,
    ):
        logger.info(f"Запись успешно добавлена по юзеру {phone}")
        await dialog_manager.switch_to(state=CustomerSG.menu)
    else:
        logger.error("Не удалось добавить запись при регистрации клиента")


async def on_balance_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session = dialog_manager.middleware_data.get("session")
    bot: Bot = dialog_manager.middleware_data.get("bot")

    result = await get_bonus_info(session=session, telegram_id=callback.from_user.id)
    bonuses, date_expire, bonus_to_expire = result
    customer = await get_customer_detail_info(
        session=session, telegram_id=callback.from_user.id
    )
    visits = customer.visits
    percent_cashback = customer.percent_cashback

    if date_expire:
        date_expire: datetime = date_expire.strftime("%d.%m.%Y")
        await bot.send_message(
            chat_id=callback.from_user.id,
            text=i18n.customer.balance.message(
                current_balance=bonuses,
                date_expire=date_expire,
                balance_to_expire=bonus_to_expire,
                visits=visits,
                percent_cashback=percent_cashback,
            ),
        )
    else:
        await bot.send_message(
            chat_id=callback.from_user.id, text=i18n.customer.no.balance.message()
        )
        logger.info(
            f"Баллы просрочены или равные нулю. {bonuses, date_expire, bonus_to_expire}"
        )
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_gifts_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    text = i18n.customer.catalog.message()
    button = i18n.customer.catalog.button()
    link = i18n.customer.catalog.link()
    kb = get_kb(
        ((button, link)),
    )
    await callback.message.answer(text=text, reply_markup=kb).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_delivery_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    text = i18n.customer.delivery.message()
    bot: Bot = dialog_manager.middleware_data.get("bot")
    button = i18n.customer.delivery.button()
    link = i18n.customer.delivery.link()
    kb = get_kb([button, link])
    await callback.message.answer(text=text, reply_markup=kb).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_loayalty_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    text = i18n.customer.loyalty.message()
    button = i18n.customer.delivery.button()
    link = i18n.customer.delivery.link()
    kb = get_kb([button, link])
    await callback.message.answer(text=text, reply_markup=kb).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_partnership_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    text = i18n.customer.partnership.info.message()
    await callback.message.answer(text=text).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_help_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    text = i18n.customer.support.message()
    await callback.message.answer(text=text).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_catalog_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    media = convert_media_to_group()
    await callback.message.answer_media_group(media=media).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE


async def on_about_selected(
    callback: CallbackQuery, widget: Button, dialog_manager: DialogManager
):
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    bot: Bot = dialog_manager.middleware_data.get("bot")
    text = i18n.customer.about.info.message()
    button = i18n.customer.delivery.button()
    link = i18n.customer.delivery.link()
    kb = get_kb([button, link])
    await callback.message.answer(text=text, reply_markup=kb).as_(bot)
    dialog_manager.show_mode = ShowMode.NO_UPDATE
