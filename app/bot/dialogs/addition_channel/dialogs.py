from aiogram.types import ContentType
from aiogram_dialog import Dialog, ShowMode, Window
from aiogram_dialog.widgets.text import Format, Case
from aiogram_dialog.widgets.kbd import (
    Url,
    SwitchTo,
    Select,
    Group,
    Back,
    Start,
    Checkbox,
)
from aiogram_dialog.widgets.input import TextInput, MessageInput

from magic_filter import F

from app.bot.states.manager.addition_channel import AdditionToChannelSG
from app.bot.states.manager.manager import ManagerSG
from .getters import (
    get_channel_settings,
    get_data_for_caption,
    get_data_for_delete,
    get_url_info,
    get_data_for_set_caption,
)
from .handlers import (
    add_caption_to_channel,
    auto_caption_changed,
    check_admin_status,
    delete_caption,
    delete_channel_from_bot,
    handle_error_caption,
    on_channel_selected,
    validate_channel,
)


dialog_addition_channel = Dialog(
    Window(
        Case(
            {
                1: Format("{channel_exists_message}"),
                0: Format("{channel_not_exists_message}"),
            },
            selector="channel_exists",
        ),
        Format("{instruction_add_channel}"),
        Group(
            Select(
                Format("{item[1]}"),  # Структура item:
                # [channel_id, channel_name,channel_username,channel_link,admin_id,]
                id="selected_channel",
                item_id_getter=lambda x: x[0],
                items="channels",
                on_click=on_channel_selected,
            ),
            width=2,
            when="channel_exists",
        ),
        Url(
            text=Format("{url_button_name}"),
            url=Format("{url_button}"),
            id="add_channel_pressed",
        ),
        Start(
            Format("{back}"), id="back_to_menu", state=ManagerSG.start, when="is_admin"
        ),
        TextInput(
            id="chhanel_check_bot_status",
            type_factory=validate_channel,
            on_success=check_admin_status,
        ),
        state=AdditionToChannelSG.start,
        getter=get_url_info,
    ),
    # Окно настройки канала
    Window(
        Format("{channel_settings_desc}"),
        Group(
            SwitchTo(
                text=Format("{channel_delete_from_bot_desc}"),
                id="delete_channel_selected",
                state=AdditionToChannelSG.delete_bot_from_channel,
            ),
            SwitchTo(
                text=Format("{channel_add_caption_desc}"),
                id="add_caption_channel",
                state=AdditionToChannelSG.add_caption_to_channel,
            ),
        ),
        Back(text=Format("{back}"), show_mode=ShowMode.DELETE_AND_SEND),
        state=AdditionToChannelSG.channel_settings,
        getter=get_channel_settings,
    ),
    # Окно удаления канала из бота
    Window(
        Format("{delete_bot_from_channel_desc}"),
        SwitchTo(
            text=Format("{channel_delete_button}"),
            id="delete_channel_done",
            state=AdditionToChannelSG.start,
            on_click=delete_channel_from_bot,
            show_mode=ShowMode.DELETE_AND_SEND,
        ),
        Back(text=Format("{back}"), show_mode=ShowMode.DELETE_AND_SEND),
        state=AdditionToChannelSG.delete_bot_from_channel,
        getter=get_data_for_delete,
    ),
    # Окно предложения добавления подписи к постам канала и конфигурации подписи
    Window(
        Format(text="{not_exists}", when=~F["caption_exists"]),
        SwitchTo(
            text=Format("{add}"),
            id="add_caption_btn_pressed",
            state=AdditionToChannelSG.add_caption_to_channel,
            when=~F["caption_exists"],
        ),
        Format(text="{caption}", when=F["caption"]),
        Group(
            SwitchTo(
                Format("{delete}"),
                id="delete_caption_selected",
                state=AdditionToChannelSG.start,
                on_click=delete_caption,
            ),
            Checkbox(
                checked_text=Format("{turn_on}"),
                unchecked_text=Format("{turn_off}"),
                id="checkbox_caption_selected",
                on_state_changed=auto_caption_changed,
                default=True,
            ),
            width=1,
        ),
        SwitchTo(
            text=Format("{back}"),
            id="back_from_config_caption",
            state=AdditionToChannelSG.channel_settings,
            show_mode=ShowMode.DELETE_AND_SEND,
        ),
        state=AdditionToChannelSG.config_caption,
        getter=get_data_for_caption,
    ),
    # Окно записи текста в подпись
    Window(
        Format("{channel_caption_wait}"),
        TextInput(
            id="added_auto_caption",
            on_success=add_caption_to_channel,
        ),
        MessageInput(func=handle_error_caption, content_types=ContentType.ANY),
        state=AdditionToChannelSG.add_caption_to_channel,
        getter=get_data_for_set_caption,
    ),
)
