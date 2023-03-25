import json
import logging

from radarr import api as radarr_api
from rich.logging import RichHandler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, error
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from tmdb import api as tmdb_api

from rbot.conf import settings
from rbot.decorators import restricted
from rbot.storage.models import Movie
from rbot.storage.redis import (
    clear_redis,
    read_one_movie_from_redis,
    write_movies_to_redis,
)

logging.basicConfig(
    level="INFO",
    format=settings.LOG_FORMAT,
    datefmt=settings.DATE_FORMAT,
    handlers=[RichHandler()],
)
log = logging.getLogger(__name__)


async def send_typing_action(bot: Bot, chat_id: int) -> None:
    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)


async def accepted_movie(data: dict[str, str]) -> str:
    movie_id = data["movie_id"]
    response = await radarr_api.add_movie_to_radarr(movie_id)
    return response


async def show_next_movie(data: dict[str, str]) -> tuple[int, Movie] | None:
    idx = int(data["idx"])
    movie = await read_one_movie_from_redis(idx)
    if movie:
        return idx + 1, movie
    return None

async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text, disable_notification=True)


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
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot
    await bot.send_chat_action(action=ChatAction.TYPING, chat_id=chat_id)

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
    bot = application.bot
    await bot.send_chat_action(
        action=ChatAction.TYPING, chat_id=settings.TELEGRAM_EDUZEN_ID
    )
    await send_message(bot, settings.TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> int:
    application = (
        ApplicationBuilder().token(settings.TELEGRAM_TOKEN).post_init(post_init).build()
    )
    help_handler = CommandHandler("help", help)

    application.add_handler(help_handler)

    search_handler = CommandHandler("search", search)
    application.add_handler(search_handler)

    movie_handler = CommandHandler("movie", movie)
    application.add_handler(movie_handler)

    callback_handler = CallbackQueryHandler(callback)
    application.add_handler(callback_handler)

    try:
        application.run_polling()
    except Exception:
        log.exception("Error while polling")
        return -1

    return 0


if __name__ == "__main__":
    exit(main())
