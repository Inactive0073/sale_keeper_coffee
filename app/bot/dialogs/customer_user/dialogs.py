from aiogram.types import ContentType
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import (
    Group,
    Button,
    Row,
    RequestContact,
    Start,
)
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram_dialog.widgets.markup.reply_keyboard import ReplyKeyboardFactory

from app.bot.states.admin import AdminSG
from app.bot.states.customer.start import CustomerSG
from .getters import get_common_data, get_customer_menu_data
from .filters import ContactFilter
from .handlers import (
    on_about_selected,
    on_balance_selected,
    on_catalog_selected,
    on_gifts_selected,
    on_help_selected,
    on_loayalty_selected,
    on_partnership_selected,
    process_gender_selected,
    process_invalid_birthday,
    process_invalid_phone,
    process_succes_birthday,
    process_succes_contact,
    process_succes_email,
    process_succes_name,
    process_succes_surname,
)
from .services import check_birthday_format


customer_dialog = Dialog(
    Window(
        Format("{hello_guest}"),
        RequestContact(Format("{meeting_phone_message}")),
        MessageInput(
            func=process_succes_contact,
            content_types=ContentType.CONTACT,
            filter=ContactFilter(),
        ),
        MessageInput(func=process_invalid_phone, content_types=ContentType.ANY),
        state=CustomerSG.start,
        markup_factory=ReplyKeyboardFactory(
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    ),
    Window(
        Format("{meeting_name_message}"),
        TextInput(
            id="expecting_name",
            on_success=process_succes_name,
        ),
        state=CustomerSG.name,
    ),
    Window(
        Format("{meeting_surname_message}"),
        TextInput(
            id="expecting_surname",
            on_success=process_succes_surname,
        ),
        state=CustomerSG.surname,
    ),
    Window(
        Format("{meeting_email_message}"),
        TextInput(id="expecting_name", on_success=process_succes_email),
        state=CustomerSG.email,
    ),
    Window(
        Format("{meeting_birthday_message}"),
        TextInput(
            id="expecting_name",
            on_success=process_succes_birthday,
            type_factory=check_birthday_format,
            on_error=process_invalid_birthday,
        ),
        state=CustomerSG.birthday,
    ),
    Window(
        Format("{meeting_gender_message}"),
        Row(
            Button(
                Format("{meeting_gender_m_button}"),
                id="m_gender_selected",
                on_click=process_gender_selected,
            ),
            Button(
                Format("{meeting_gender_f_button}"),
                id="f_gender_selected",
                on_click=process_gender_selected,
            ),
        ),
        state=CustomerSG.gender,
    ),
    # Раздел меню
    Window(
        Format("{menu_info_message}"),
        Group(
            Button(
                Format("{menu_balance_button}"),
                id="balance_selected",
                on_click=on_balance_selected,
            ),
            Button(
                Format("{menu_gifts_button}"),
                id="gifts_selected",
                on_click=on_gifts_selected,
            ),
            Button(
                text=Format("{menu_menu_button}"),
                id="menu_selected",
                on_click=on_catalog_selected,
            ),
            # Button(
            #     Format("{menu_delivery_button}"),
            #     id="delivery_selected",
            #     on_click=on_delivery_selected,
            # ),
            width=2,
        ),
        Button(
            Format("{menu_about_button}"),
            id="about_us_selected",
            on_click=on_about_selected,
        ),
        Group(
            Button(
                Format("{menu_partnership_button}"),
                id="partnership_selected",
                on_click=on_partnership_selected,
            ),
            Button(
                Format("{menu_help_button}"),
                id="help_selected",
                on_click=on_help_selected,
            ),
            Button(
                Format("{menu_loayalty_button}"),
                id="loayalty_selected",
                on_click=on_loayalty_selected,
            ),
            width=2,
        ),
        Start(
            Format("{to_admin_menu}"),
            id="to_admin_menu",
            state=AdminSG.start,
            when="is_admin",
        ),
        state=CustomerSG.menu,
        markup_factory=ReplyKeyboardFactory(
            resize_keyboard=True,
            input_field_placeholder=Format("{customer_menu_placeholder}"),
        ),
        getter=get_customer_menu_data,
    ),
    getter=get_common_data,
)
