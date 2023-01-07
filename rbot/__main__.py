from decouple import config
from rich import print
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update, helpers
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


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)

async def send_photo(bot: Bot, chat_id: int, photo: str | bytes) -> None:
    await bot.send_photo(chat_id=chat_id, photo=photo)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    args: list = context.args
    if not args:
        await send_message(bot, chat_id, "missing query")
        return

    query = " ".join(args)
    print(query)

    try:
        data = await tmdb_api.search_movie(query)
        await send_message(bot, chat_id, [movie.to_str() for movie in data])
    except Exception as e:
        print("Error while searching movie", e)
        await send_message(bot, chat_id, "Something went wrong")


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore
    bot = context.bot

    args: list = context.args
    if not args:
        await send_message(bot, chat_id, "missing movie id")
        return

    movie_id = args[0]

    try:
        movie = await tmdb_api.get_movie_detail(movie_id)
        await send_photo(bot, chat_id, movie.poster)
        await send_message(bot, chat_id, movie.to_str())
    except Exception as e:
        print("Error while getting movie detail", e)
        await send_message(bot, chat_id, "Something went wrong")


async def show_movie(update, context):
    # Movie info
    bot = context.bot
    movie_title = "Movie Title"
    movie_description = "Movie Description"
    movie_year = "2020"
    message = f"{movie_title} ({movie_year})\n{movie_description}  {url}"

    # Create the inline keyboard
    confirm_button = InlineKeyboardButton("Confirm", callback_data="confirm")
    next_button = InlineKeyboardButton("Next", callback_data="next")
    keyboard = [[confirm_button, next_button]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the message with the inline keyboard
    await update.message.reply_text(message, reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Parses the CallbackQuery and updates the message text."""
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    await query.edit_message_text(text=f"Selected option: {query.data}")

async def post_init(application: Application) -> None:
    await send_message(application.bot, TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> None | int:
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    search_handler = CommandHandler("search", search)
    application.add_handler(search_handler)

    movie_handler = CommandHandler("movie", movie)
    application.add_handler(movie_handler)

    show_movie_handler = CommandHandler("show_movie", show_movie)
    application.add_handler(show_movie_handler)

    button_callback_handler = CallbackQueryHandler(button)
    application.add_handler(button_callback_handler)

    try:
        application.run_polling()
    except Exception:
        print("Error while polling")
        raise SystemExit(1)



if __name__ == "__main__":
    exit(main())
