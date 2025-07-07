import random
from typing import TYPE_CHECKING

from aiogram.types import (
    Message,
)

from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import TextInput

from app.bot.db.models.customers import Customer
from app.bot.db.customer_requests import (
    get_bonus_info,
    get_customer_detail_info,
    add_bonus,
    deduct_bonus,
)
from ...states.waiter.start import WaiterSG
import logging
import json

if TYPE_CHECKING:
    from locales.stub import TranslatorRunner  # type: ignore

logger = logging.getLogger(__name__)


async def output_instruction(
    message: Message, widget: TextInput, dialog_manager: DialogManager, token: str
) -> None:
    await dialog_manager.switch_to(
        WaiterSG.instruction, show_mode=ShowMode.DELETE_AND_SEND
    )


async def process_phone_number(
    message: Message, widget: TextInput, dialog_manager: DialogManager, phone_number: str
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    session = dialog_manager.middleware_data.get("session")
    
    phone_number = f"+7{phone_number[1:]}" if phone_number.startswith(("8", "7")) else phone_number
    logger.info(f"User {phone_number=} has started number verify")

    customer: Customer = await get_customer_detail_info(
        session=session, phone=phone_number
    )

    if customer:
        result = await get_bonus_info(session=session, telegram_id=customer.telegram_id)
        bonuses, date_expire, bonus_to_expire = result
        date_expire = "♾" if date_expire is None else date_expire

        dialog_manager.dialog_data["has_bonus"] = bool(date_expire)
        dialog_manager.dialog_data["customer_id"] = customer.telegram_id
        dialog_manager.dialog_data["customer_balance"] = bonuses
        name = customer.i_name if customer.i_name else " "
        text = i18n.waiter.success.info.customer(
            name=name,
            balance=bonuses,
            date_expire=date_expire,
            bonus_to_expire=bonus_to_expire,
        )
        await message.answer(text=text)
        await dialog_manager.switch_to(WaiterSG.processing)
    else:
        text = i18n.waiter.invalid.info.customer()
        await message.answer(text=text)
        return


async def process_invalid_number(
    message: Message, widget, dialog_manager: DialogManager
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    await message.answer(i18n.waiter.invalid.info.customer())


async def process_adding_bonus(
    message: Message,
    widget: TextInput,
    dialog_manager: DialogManager,
    total_amount: int,
) -> None:
    session = dialog_manager.middleware_data.get("session")
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")

    customer_id = dialog_manager.dialog_data.get("customer_id")
    amount_bonus = await add_bonus(
        session=session, customer_id=customer_id, total_amount=total_amount
    )
    if amount_bonus != False:
        text = i18n.waiter.processing.adding.success(amount=amount_bonus)
        await message.answer(text)
        await dialog_manager.switch_to(WaiterSG.start)
    else:
        text = i18n.waiter.processing.adding.unsuccess()
        await message.answer(text)
        logger.info(f"Не удалось начислить баллы для юзера {customer_id}")


async def process_validate_balance(
    message: Message, widget: TextInput, dialog_manager: DialogManager, n_bonus: int
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    customer_balance = dialog_manager.dialog_data.get("customer_balance")
    customer_id = dialog_manager.dialog_data.get("customer_id")

    if customer_balance < n_bonus:
        await message.answer(i18n.waiter.processing.subtracting.not_.enough())
    else:
        guess_number = str(random.randint(1000,9999))
        await message.bot.send_message(chat_id=customer_id, text=i18n.waiter.to.client.msg(code=guess_number))
        dialog_manager.dialog_data["guess_number"] = guess_number
        dialog_manager.dialog_data["customer_n_bonus"] = n_bonus
        await dialog_manager.switch_to(state=WaiterSG.subtracting)
    

async def process_subtract_bonus(
    message: Message, widget: TextInput, dialog_manager: DialogManager, code: int
) -> None:
    i18n: TranslatorRunner = dialog_manager.middleware_data.get("i18n")
    correct_code = int(dialog_manager.dialog_data.get("guess_number"))
    session = dialog_manager.middleware_data.get("session")
    
    if code != correct_code:
        await message.answer(i18n.waiter.invalid.code.msg())
        return

    customer_id = dialog_manager.dialog_data.get("customer_id")
    n_bonus = dialog_manager.dialog_data.get("customer_n_bonus")
    result = await deduct_bonus(
        session=session, customer_id=customer_id, amount=n_bonus
    )
    if result != False:
        text = i18n.waiter.processing.subtracting.success()
        await message.answer(text)
        await dialog_manager.switch_to(WaiterSG.start)
    else:
        text = i18n.waiter.processing.subtracting.unsuccess()
        await message.answer(text)
