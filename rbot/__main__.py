import logging

from decouple import config
from rich import print
from rich.logging import RichHandler
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)
from tmdb import api as tmdb_api

TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)
FORMAT = "%(message)s"

logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)


async def next_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


async def confirm_movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)


async def send_buttons(
    bot: Bot, chat_id: int, text: str, buttons: list[list[InlineKeyboardButton]]
) -> None:
    if not buttons:
        confirm_button = InlineKeyboardButton("Confirm", callback_data="confirm_movie")
        next_button = InlineKeyboardButton("Next", callback_data="next_movie")
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
        for movie in data:
            log.info(movie.json())

            await send_photo(bot, chat_id, movie.poster, caption=str(movie))
        else:
            await send_message(bot, chat_id, "No movie found")
    except Exception as e:
        print("Error while searching movie", e)
        await send_message(bot, chat_id, "Something went wrong")


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
    except Exception as e:
        print("Error while getting movie detail", e)
        await send_message(bot, chat_id, "Something went wrong")


async def post_init(application: Application) -> None:
    await send_message(application.bot, TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> None | int:  # type: ignore
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    search_handler = CommandHandler("search", search)
    application.add_handler(search_handler)

    movie_handler = CommandHandler("movie", movie)
    application.add_handler(movie_handler)

    next_movie_callback_handler = CallbackQueryHandler(next_movie)
    application.add_handler(next_movie_callback_handler)

    confirm_movie_callback_handler = CallbackQueryHandler(confirm_movie)
    application.add_handler(confirm_movie_callback_handler)

    try:
        return application.run_polling()
    except Exception:
        log.exception("Error while polling")
        return -1


if __name__ == "__main__":
    exit(main())
