import os
import logging
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

TOKEN = os.getenv("TOKEN")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

client = httpx.AsyncClient()


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(context.args)
    response = await client.get(f"{TMDB_URL}&query={context.args[0]}")
    #print(response.json())
    await context.bot.send_message(chat_id=update.effective_chat.id, text="e")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="I'm a bot, please talk to me!")


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)

    start_handler = CommandHandler('search', search)
    application.add_handler(start_handler)

    try:
        application.run_polling()
    except Exception:
        logger.exception("Error while polling")

if __name__ == '__main__':
    exit(main())
