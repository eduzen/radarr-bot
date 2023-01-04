from decouple import config
from rich import print
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    Bot,
    CommandHandler,
    ContextTypes,
)
from tmdb import api as tmdb_api

TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)


async def send_message(bot: Bot, chat_id: int, text: str) -> None:
    await bot.send_message(chat_id=chat_id, text=text)


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
        await send_message(bot, chat_id, data)
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
        data = await tmdb_api.get_movie_detail(movie_id)
        await send_message(bot, chat_id, data)
    except Exception as e:
        print("Error while getting movie detail", e)
        await send_message(bot, chat_id, "Something went wrong")


async def post_init(application: Application) -> None:
    await send_message(application.bot, TELEGRAM_EDUZEN_ID, "Bot started!")


def main() -> None | int:
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    search_handler = CommandHandler("search", search)
    application.add_handler(search_handler)

    movie_handler = CommandHandler("movie", movie)
    application.add_handler(movie_handler)

    try:
        application.run_polling()
    except Exception:
        print("Error while polling")
        raise SystemExit(1)


if __name__ == "__main__":
    exit(main())
