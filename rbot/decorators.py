import logging
from functools import wraps

from decouple import Csv, config
from telegram import Update, User
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)

LIST_OF_ADMINS = config("LIST_OF_ADMINS", cast=Csv(int))


async def get_userdata(user: User) -> tuple[str, str]:
    return user.id, user.to_json()


def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        func_name = func.__name__
        user_id, user_data = await get_userdata(update.effective_user)
        if user_id not in LIST_OF_ADMINS:
            log.warning(f"'{func_name}' Access Denied to: {user_data}")
            return
        log.info(f"'{func_name}' Access Granted to: {user_data}")
        return await func(update, context)

    return wrapped
