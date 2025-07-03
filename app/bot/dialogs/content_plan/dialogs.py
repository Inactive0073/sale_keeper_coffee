from typing import Callable

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Button,
    Back,
    Select,
    Row,
    Start,
    ScrollingGroup,
)

from app.bot.states.manager import ManagerSG, ContentSG
from app.bot.utils.schemas.models import PostData
from .calendar_ import CustomCalendar
from .getters import content_data, content_posts_data, content_today_data
from .handlers import (
    on_date_selected,
    on_post_selected,
    type_selected,
    on_cancel_selected,
)


post_id_getter: Callable[[PostData], str] = lambda item: item.schedule_id

content_dialog = Dialog(
    Window(
        Format("{content_hello_msg}"),
        Row(
            SwitchTo(
                Format("{content_bot_btn}"),
                id="bot",
                state=ContentSG.bot,
                on_click=type_selected,
            ),
            SwitchTo(
                Format("{content_channel_btn}"),
                id="channel",
                state=ContentSG.channel,
                on_click=type_selected,
            ),
        ),
        Start(Format("{main_menu}"), id="main_menu", state=ManagerSG.start),
        state=ContentSG.start,
    ),
    # окно контента бота
    Window(
        Format("{content_msg}"),
        CustomCalendar(id="calendar", on_click=on_date_selected),
        SwitchTo(Format("{back}"), id="__back__", state=ContentSG.start),
        state=ContentSG.bot,
        getter=content_posts_data,
    ),
    # окно контента канала
    Window(
        Format("{content_msg}"),
        CustomCalendar(id="calendar", on_click=on_date_selected),
        SwitchTo(Format("{back}"), id="__back__", state=ContentSG.start),
        state=ContentSG.channel,
        getter=content_posts_data,
    ),
    # окно контента на сегодня
    Window(
        Format("{today_info_msg}"),
        ScrollingGroup(
            Select(
                Format("{item.scheduled_time_fmt} - {item.text}"),
                id="s_calendar",
                item_id_getter=post_id_getter,
                items="posts",
                on_click=on_post_selected,
            ),
            id="sg_calendar",
            width=1,
            height=5,
            hide_on_single_page=True,
        ),
        SwitchTo(Format("{back}"), id="__back__", state=ContentSG.bot),
        getter=content_today_data,
        state=ContentSG.today_info,
    ),
    # окно работы с постами на выбранный период
    Window(
        Format("{process_selected_post_msg}"),
        Button(Format("{to_cancel}"), id="delete_post", on_click=on_cancel_selected),
        Back(Format("{back}")),
        state=ContentSG.process_selected,
    ),
    getter=content_data,
)
