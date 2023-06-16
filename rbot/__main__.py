import logging

from rich.logging import RichHandler
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, CommandHandler

from rbot.conf import settings
from rbot.handlers import callback, help, movie, search, serie
from rbot.utils import post_init

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format=settings.LOG_FORMAT,
    datefmt=settings.DATE_FORMAT,
    handlers=[RichHandler()],
)


log = logging.getLogger(__name__)


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

    serie_handler = CommandHandler("serie", serie)
    application.add_handler(serie_handler)

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
