import json
import logging

import redis.asyncio as redis
from decouple import config
from radarr import api as radarr_api
from rich.logging import RichHandler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, error
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from tmdb import api as tmdb_api

from rbot.decorators import restricted
from rbot.models import Movie

TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)
REDIS_HOST = config("REDIS_HOST")
REDIS_URL = config("REDIS_URL")
FORMAT = "%(message)s"

logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)


async def write_movies_to_redis(movies: list[Movie]) -> None:
    client = await redis.from_url(REDIS_URL)

    async with client.pipeline(transaction=True) as pipe:
        for idx, movie in enumerate(movies):
            await pipe.set(idx, movie.json()).execute()


async def read_one_movie_from_redis(idx: int) -> Movie | None:
    try:
        client = await redis.from_url(REDIS_URL)
        movie = await client.get(idx)
        movie = json.loads(movie)
        return Movie(**movie)
    except Exception:
        log.exception("Error while reading from redis")


@restricted
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    try:
        await query.answer()
        log.info("Callback query answered, data: %s", query.data)
        dict_data = json.loads(query.data)

        if "movie_id" in dict_data.keys():
            movie_id = dict_data["movie_id"]
            response = await radarr_api.add_movie_to_radarr(movie_id)
            await query.edit_message_text(text=response)
        else:
            idx = dict_data["idx"]
            movie = await read_one_movie_from_redis(idx)
            if not movie:
                await query.edit_message_text(text="No more movies found")
                return

            log.info(movie)
            await query.edit_message_text(text=movie.title)
            return

    except error.BadRequest as e:
        log.error("Error while answering callback query %s", str(e))
        send_message(context.bot, TELEGRAM_EDUZEN_ID, str(e))


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)


async def send_buttons(
    bot: Bot,
    chat_id: int,
    text: str,
    movie_id: str,
    idx: int,
    buttons: list[list[InlineKeyboardButton]] | None = None,
) -> None:
    if not buttons:
        callback_data_confirm = json.dumps({"movie_id": movie_id})
        callback_data_next = json.dumps({"idx": idx + 1})
        confirm_button = InlineKeyboardButton(
            "Confirm", callback_data=callback_data_confirm
        )
        next_button = InlineKeyboardButton("Next", callback_data=callback_data_next)
        buttons = [[confirm_button, next_button]]
    reply_markup = InlineKeyboardMarkup(buttons)

    await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)


async def send_photo(
    bot: Bot,
    chat_id: int,
    photo: str | bytes,
    caption: str,
) -> None:
    await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption)


@restricted
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

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

        try:
            await send_photo(bot, chat_id, movie.poster, caption=str(movie))
        except Exception:
            log.exception("Error while sending photo")
            await send_message(bot, chat_id, str(movie))

        await send_buttons(bot, chat_id, "Is this the movie?", movie_id=movie.id, idx=0)

    except Exception:
        log.exception("Error while searching movie")
        await send_message(bot, chat_id, "Something went wrong")


@restricted
async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

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
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    bot = context.bot

    help_text = (
        "Hello, I'm RadarrBot. I have the following commands:\n"
        "- /search <name of the movie>: search for a movie in tmdb \n"
        "- /movie <id of the movie>: search a movie based on ids \n"
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


async def post_init(application: Application) -> None:
    await send_message(application.bot, TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> None | int:  # type: ignore
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    help_handler = CommandHandler("help", help)
    application.add_handler(help_handler)

    search_handler = CommandHandler("search", search)
    application.add_handler(search_handler)

    movie_handler = CommandHandler("movie", movie)
    application.add_handler(movie_handler)

    callback_handler = CallbackQueryHandler(callback)
    application.add_handler(callback_handler)

    try:
        return application.run_polling()
    except Exception:
        log.exception("Error while polling")
        return -1


if __name__ == "__main__":
    exit(main())
