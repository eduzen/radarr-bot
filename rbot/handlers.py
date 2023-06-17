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
    show_next_result,
)

log = logging.getLogger(__name__)


@restricted
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    user_id = update.callback_query.from_user.id  # type: ignore
    log.warning("### Callback query received from %s", user_id)
    query = update.callback_query
    bot = context.bot

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise.
    # See https://core.telegram.org/bots/api#callbackquery
    try:
        await query.answer()  # type: ignore
        chat_id = query.message.chat_id  # type: ignore
        dict_data = json.loads(query.data)  # type: ignore

        if "movie_id" in dict_data.keys():
            log.warning("### Accepted Movie!")
            response = await accepted_movie(dict_data)
            await query.edit_message_text(text=response)  # type: ignore
        elif "serie_id" in dict_data.keys():
            log.warning("### Accepted Series!")
            response = await accepted_serie(dict_data)
            await query.edit_message_text(text=response)  # type: ignore
        else:
            log.warning("### Next result!")
            data = await show_next_result(dict_data)
            if not data:
                msg = "No more movies to show"
                await query.edit_message_text(text=msg)  # type: ignore
            else:
                idx, movie = data
                await query.edit_message_text(text="Loading...")  # type: ignore

                await send_movie(bot, chat_id, movie, idx)  # type: ignore
    except error.BadRequest as e:
        log.exception("Error while answering callback query")
        await send_message(bot, settings.TELEGRAM_EDUZEN_ID, str(e))


@restricted
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("# Entering search handler...")
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)
    await clear_redis()

    args: list[str] | None = context.args
    if not args:
        await send_message(
            bot,
            chat_id,
            "Probably you missed the search word. Try again with /search <movie name>",
        )
        return None

    query = " ".join(args)
    log.debug(f"# Search parameters {query}")

    try:
        data = await tmdb_api.search_movie(query)
        if not data:
            await send_message(bot, chat_id, "No movie found")
            return

        movie = data[0]
        await write_movies_to_redis(data)
        await send_movie(bot, chat_id, movie)

    except Exception:
        log.exception("# Error while searching movie")
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
        await send_buttons(
            bot, chat_id, "Is this the movie?", callback_data=movie.id  # type: ignore
        )
    except Exception:
        log.exception("Error while getting movie detail")
        await send_message(bot, chat_id, "Something went wrong")


@restricted
async def series(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log.info("### Entering series handler...")
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)

    args: list[str] | None = context.args
    if not args:
        await send_message(
            bot,
            chat_id,
            "Probably you missed the search word. Try again with /series <series name>",
        )
        return None

    query_serie = " ".join(args)
    log.info(f"### Search parameters {query_serie}")

    try:
        data = await tmdb_api.search_series(query_serie)
        if not data:
            await send_message(bot, chat_id, "No series found")
            return

        series = data[0]
        await write_movies_to_redis(data)
        await send_serie(bot, chat_id, series)

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
        "- /series <name of the series>: search for a series in tmdb \n"
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
