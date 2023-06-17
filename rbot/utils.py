import json
import logging

from radarr import api as radarr_api
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.ext import Application

from rbot.conf import settings
from rbot.storage.models import Movie, Series
from rbot.storage.redis import read_one_result_from_redis

log = logging.getLogger(__name__)


async def send_typing_action(bot: Bot, chat_id: int) -> None:
    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)


async def accepted_movie(data: dict[str, str]) -> str:
    movie_id = data["movie_id"]
    response = await radarr_api.add_movie_to_radarr(movie_id)
    return response


async def accepted_serie(data: dict[str, str]) -> str:
    serie_id = data["serie_id"]
    response = await radarr_api.add_serie_to_radarr(serie_id)
    return response


async def show_next_result(data: dict[str, str]) -> tuple[int, Movie | Series] | None:
    idx = int(data["idx"])
    result = await read_one_result_from_redis(idx)
    if result:
        return idx + 1, result
    return None


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)


async def send_buttons(
    bot: Bot,
    chat_id: int,
    text: str,
    idx: int,
    movie_id: str | None = None,
    serie_id: str | None = None,
    buttons: list[list[InlineKeyboardButton]] | None = None,
) -> None:
    if not buttons:
        if movie_id:
            callback_data_confirm = json.dumps({"movie_id": movie_id})
        else:
            callback_data_confirm = json.dumps({"serie_id": serie_id})
        callback_data_next = json.dumps({"idx": idx + 1})
        confirm_button = InlineKeyboardButton(
            "Confirm", callback_data=callback_data_confirm
        )
        next_button = InlineKeyboardButton("Next", callback_data=callback_data_next)
        buttons = [[confirm_button, next_button]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        disable_notification=True,
    )


async def send_photo(
    bot: Bot,
    chat_id: int,
    photo: str | bytes,
    caption: str,
) -> None:
    await bot.send_photo(
        chat_id=chat_id, photo=photo, caption=caption, disable_notification=True
    )


async def send_movie(bot: Bot, chat_id: int, movie: Movie, idx: int = 0) -> None:
    try:
        await send_photo(
            bot,
            chat_id,
            movie.poster,
            caption=str(movie),
        )
    except Exception:
        log.exception("Error while sending photo")
        await send_message(bot, chat_id, str(movie))

    await send_buttons(bot, chat_id, "Is this the movie?", movie_id=movie.id, idx=idx)


async def send_serie(bot: Bot, chat_id: int, series: Series, idx: int = 0) -> None:
    try:
        await send_photo(
            bot,
            chat_id,
            series.poster,
            caption=str(series),
        )
    except Exception:
        log.exception("Error while sending photo")
        await send_message(bot, chat_id, str(series))

    await send_buttons(bot, chat_id, "Is this the series?", serie_id=series.id, idx=idx)


async def post_init(application: Application) -> None:
    bot = application.bot
    await bot.send_chat_action(
        action=ChatAction.TYPING, chat_id=settings.TELEGRAM_EDUZEN_ID
    )
    await send_message(bot, settings.TELEGRAM_EDUZEN_ID, "Bot started!")
