import logging
from functools import wraps

from telegram import Update, User
from telegram.ext import ContextTypes

from rbot.conf import settings

log = logging.getLogger(__name__)


async def get_userdata(user: User) -> tuple[str, str]:
    return user.id, user.to_json()


def restricted(func):
    @wraps(func)
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        func_name = func.__name__
        user_id, user_data = await get_userdata(update.effective_user)
        if user_id not in settings.LIST_OF_ADMINS:
            log.warning(f"'{func_name}' Access Denied to: {user_data}")
            return
        log.info(f"'{func_name}' Access Granted to: {user_data}")
        return await func(update, context)

    return wrapped
