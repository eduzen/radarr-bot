import logging
from typing import Any

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

TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)
FORMAT = "%(message)s"

logging.basicConfig(
    level="INFO", format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)
log = logging.getLogger(__name__)


@restricted
async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    try:
        await query.answer()
        log.info("Callback query answered, data: %s", query.data)
        tmdb_id = query.data

        if tmdb_id == "next":
            await query.edit_message_text(text="Next")
            return

        response = await radarr_api.add_movie_to_radarr(query.data)
        await query.edit_message_text(text=response)

    except error.BadRequest as e:
        log.error("Error while answering callback query %s", str(e))
        send_message(context.bot, TELEGRAM_EDUZEN_ID, str(e))


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)


async def send_buttons(
    bot: Bot,
    chat_id: int,
    text: str,
    callback_data: str | dict[str, Any],
    buttons: list[list[InlineKeyboardButton]] | None = None,
) -> None:
    if not buttons:
        confirm_button = InlineKeyboardButton("Confirm", callback_data=callback_data)
        next_button = InlineKeyboardButton("Next", callback_data="next")
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

        for movie in data[:1]:
            try:
                await send_photo(bot, chat_id, movie.poster, caption=str(movie))
            except Exception:
                log.error("Error while sending photo")
                await send_message(bot, chat_id, str(movie))

            await send_buttons(
                bot, chat_id, "Is this the movie?", callback_data=movie.id
            )
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
    except Exception:
        log.exception("Error while getting movie detail")
        await send_message(bot, chat_id, "Something went wrong")


async def post_init(application: Application) -> None:
    await send_message(application.bot, TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> None | int:  # type: ignore
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

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
