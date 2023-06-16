from decouple import Csv, config

# REDIS_HOST = config("REDIS_HOST", cast=str)
REDIS_URL = config("REDIS_URL", cast=str)

LIST_OF_ADMINS = config("LIST_OF_ADMINS", cast=Csv(int))

TELEGRAM_TOKEN = config("TELEGRAM_TOKEN", cast=str)

TELEGRAM_EDUZEN_ID = config("TELEGRAM_EDUZEN_ID", cast=int)

LOG_FORMAT = "%(message)s"

DATE_FORMAT = "[%Y-%m-%d %X]"

RADARR_API_KEY = config("RADARR_API_KEY", cast=str)
RADARR_BASE_URL = config("RADARR_URL", cast=str)  # http://radarr.local/api/v3/
RADARR_ROOT_FOLDER = "/media-center/movies/"
QUALITY_PROFILE_ANY = 1  # http://radarr.local/api/v3/qualityprofile

LOG_LEVEL = config("LOG_LEVEL", default="INFO", cast=str)
