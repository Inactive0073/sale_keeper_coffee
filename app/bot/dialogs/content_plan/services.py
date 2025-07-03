from typing import Any
from app.bot.utils.schemas import PostData
from app.bot.db.models.schedule_post import SchedulePost

from datetime import timedelta, timezone, datetime


def parse_post_data(
    data: list[SchedulePost], tzinfo=timezone(timedelta(hours=3))
) -> list[dict[str, Any]]:
    posts = []
    for post in data:
        scheduled_time_utc = post.scheduled_time.replace(tzinfo=timezone.utc)
        scheduled_time = scheduled_time_utc.astimezone(tzinfo)
        scheduled_time_fmt = scheduled_time.strftime("%H:%M")
        posts.append(
            PostData(
                text=post.post_message,
                schedule_id=post.schedule_id,
                scheduled_time=scheduled_time,
                scheduled_time_fmt=scheduled_time_fmt,
                keyboard=post.data_json.get("keyboard"),
                has_spoiler=post.data_json.get("has_spoiler"),
                disable_notification=post.data_json.get("disable_notification"),
                file_id=post.data_json.get("file_id"),
            ).data_python
        )

    return posts


def find_selected_posts(posts: list[PostData], selected_date: datetime):
    result = []
    for post in posts:
        if post.scheduled_time.date() == selected_date.date():
            result.append(post)
    return result


def get_dates_with_posts(posts: list[PostData]) -> set[str]:
    return {post.scheduled_time.date() for post in posts}
