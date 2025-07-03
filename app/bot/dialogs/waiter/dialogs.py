from aiogram import F
from aiogram.types import Message
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import (
    Group,
    SwitchTo,
    Start,
    StubScroll,
    NumberedPager,
)
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.media import DynamicMedia
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory

from typing import Callable

from app.bot.states.admin import AdminSG

from ...states.waiter.start import WaiterSG
from .getters import get_common_data, get_processing_guest_data, paging_getter
from .handlers import (
    process_phone_number,
    process_invalid_number,
    process_adding_bonus,
    process_subtract_bonus,
)
from .constants import ID_STUB_SCROLL


is_digit: Callable[[Message], bool] = lambda msg: msg.text.isdigit

waiter_dialog = Dialog(
    Window(
        Format("{hello_waiter}"),
        Start(
            Format("{to_admin_menu}"),
            id="to_admin_menu",
            state=AdminSG.start,
            when="is_admin",
        ),
        TextInput(id="process_phone_number", type_factory=str, on_success=process_phone_number, filter=is_digit),
        MessageInput(func=process_invalid_number),
        state=WaiterSG.start,
        markup_factory=ReplyKeyboardFactory(
            resize_keyboard=True,
            input_field_placeholder=Const("Выберите пункт меню"),
        ),
    ),
    # начисление или списание бонусов
    Window(
        Format("{process_guest_message}"),
        Group(
            SwitchTo(
                Format("{add_bonus_button}"),
                id="on_add_selected",
                state=WaiterSG.adding,
            ),
            SwitchTo(
                Format("{subtract_bonus_button}"),
                id="on_subtract_selected",
                state=WaiterSG.subtracting,
                when=F["dialog_data"]["has_bonus"],
            ),
            width=2,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=WaiterSG.start),
        state=WaiterSG.processing,
        getter=get_processing_guest_data,
    ),
    Window(
        Format("{adding_instruction}"),
        TextInput(
            id="adding_bonus_amount", type_factory=int, on_success=process_adding_bonus
        ),
        state=WaiterSG.adding,
        getter=get_processing_guest_data,
    ),
    Window(
        Format("{subtracting_instruction}"),
        TextInput(
            id="subtracting_bonus_amount",
            type_factory=int,
            on_success=process_subtract_bonus,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=WaiterSG.start),
        state=WaiterSG.subtracting,
        getter=get_processing_guest_data,
    ),
    # окно демо инструкции для официанта
    Window(
        Format("{instruction_message}"),
        Format("{pagination_message}"),
        DynamicMedia(selector="media_file"),
        StubScroll(id=ID_STUB_SCROLL, pages="pages"),
        NumberedPager(scroll=ID_STUB_SCROLL),
        SwitchTo(Format("{back}"), id="__back__", state=WaiterSG.start),
        state=WaiterSG.instruction,
        getter=paging_getter,
        preview_data=paging_getter,
    ),
    getter=get_common_data,
)
