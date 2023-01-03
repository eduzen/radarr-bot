from decouple import config
from rich import print
from telegram import Update
from telegram.ext import Application, ApplicationBuilder, CommandHandler, ContextTypes
from tmdb import api as tmdb_api

TOKEN = config("TELEGRAM_TOKEN")
TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore

    args: list = context.args
    if not args:
        await context.bot.send_message(chat_id=chat_id, text="missing query")
        return

    query = " ".join(args)
    print(query)

    try:
        data = await tmdb_api.search_movie(query)
        await context.bot.send_message(chat_id=chat_id, text=data)
    except Exception as e:
        print("Error while searching movie", e)
        await context.bot.send_message(chat_id=chat_id, text="Something went wrong")


async def movie(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id  # type: ignore

    args: list = context.args
    if not args:
        await context.bot.send_message(chat_id=chat_id, text="missing movie id")
        return

    movie_id = args[0]

    try:
        data = await tmdb_api.get_movie_detail(movie_id)
        await context.bot.send_message(chat_id=chat_id, text=data)
    except Exception as e:
        print("Error while getting movie detail", e)
        await context.bot.send_message(chat_id=chat_id, text="Something went wrong")


async def post_init(application: Application) -> None:
    await application.bot.send_message(chat_id=TELEGRAM_EDUZEN_ID, text="Bot started!")


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
