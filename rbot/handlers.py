import json
import logging

from decorators import restricted
from storage.redis import clear_redis, write_movies_to_redis
from telegram import Update, error
from telegram.constants import ChatAction
from telegram.ext import ContextTypes
from tmdb import api as tmdb_api

from rbot.conf import settings
from rbot.utils import (
    accepted_movie,
    accepted_serie,
    send_buttons,
    send_message,
    send_movie,
    send_photo,
    send_serie,
    show_next_movie,
)

log = logging.getLogger(__name__)


@restricted
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query
    bot = context.bot

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    try:
        await query.answer()
        chat_id = query.message.chat_id

        await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)

        log.info("Callback query answered, data: %s", query.data)
        dict_data = json.loads(query.data)

        if "movie_id" in dict_data.keys():
            response = await accepted_movie(dict_data)
            await query.edit_message_text(text=response)
        elif "serie_id" in dict_data.keys():
            response = await accepted_serie(dict_data)
            await query.edit_message_text(text=response)
        else:
            data = await show_next_movie(dict_data)
            if not data:
                await query.edit_message_text(text="No more movies to show")
            else:
                idx, movie = data
                await query.edit_message_text(text="Loading...")

                await send_movie(bot, chat_id, movie, idx)
    except error.BadRequest as e:
        log.exception("Error while answering callback query")
        await send_message(bot, settings.TELEGRAM_EDUZEN_ID, str(e))


@restricted
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)
    await clear_redis()

    args: list[str] | None = context.args
    if not args:
        await send_message(bot, chat_id, "missing query")
        return

    query = " ".join(args)
    log.debug(query)

    try:
        data = await tmdb_api.search_movie(query)
        if not data:
            await send_message(bot, chat_id, "No movie found")
            return

        movie = data[0]
        await write_movies_to_redis(data)
        await send_movie(bot, chat_id, movie)

    except Exception:
        log.exception("Error while searching movie")
        await send_message(bot, chat_id, "Something went wrong")


@restricted
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)
    await clear_redis()

    args: list[str] | None = context.args
    if not args:
        await send_message(bot, chat_id, "missing movie id")
        return

    movie_id = args[0]

    try:
        movie = await tmdb_api.get_movie_detail(movie_id)
        await send_photo(bot, chat_id, movie.poster, caption=str(movie))
        await send_buttons(bot, chat_id, "Is this the movie?", callback_data=movie.id)
    except Exception:
        log.exception("Error while getting movie detail")
        await send_message(bot, chat_id, "Something went wrong")


@restricted
async def serie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)

    args: list[str] | None = context.args
    if not args:
        error_msg = "Please write the name of the serie you want to search"
        await send_message(bot, chat_id, error_msg)
        return

    query_serie = " ".join(args)
    log.debug(query_serie)

    try:
        data = await tmdb_api.search_serie(query_serie)
        if not data:
            await send_message(bot, chat_id, "No serie found")
            return

        serie = data[0]
        await write_movies_to_redis(data)
        await send_serie(bot, chat_id, serie)

    except Exception:
        log.exception("Error while searching movie")
        await send_message(bot, chat_id, "Something went wrong")


@restricted
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot
    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)

    help_text = (
        "Hello, I'm RadarrBot. I have the following commands:\n"
        "- /search <name of the movie>: search for a movie in tmdb \n"
        "- /movie <id of the movie>: search a movie based on ids \n"
        "- /serie <name of the serie>: search for a serie in tmdb \n"
    )
    await send_message(bot, chat_id, help_text)
    help_text = "So if you know the id of the movie, use /movie and id of the movie"
    await send_message(bot, chat_id, help_text)
    help_text = (
        "But, if you don't the id of the movie, use `/search <name of the movie>` "
        "to lookup movies with that name.\n"
        "You can find the ids of the movies in https://www.themoviedb.org/ "
        "for example in https://www.themoviedb.org/movie/877269-strange-world "
        "we only the numbders in the url: 877269\n"
    )
    await send_message(bot, chat_id, help_text)
