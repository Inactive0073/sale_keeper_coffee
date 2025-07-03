from aiogram.fsm.state import State, StatesGroup


class PostingSG(StatesGroup):
    watch_text = State()
    creating_post = State()  # Основное окно создания поста
    editing_text = State()
    add_url = State()
    set_time = State()
    set_notify = State()
    media = State()
    toggle_comments = State()
    push_now = State()
    push_later = State()
    select_channels = State()
    show_posted_status = State()
    show_sended_status = State()
