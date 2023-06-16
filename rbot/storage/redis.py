import json
import logging

import redis.asyncio as redis

from rbot.conf import settings

from .models import Movie, Serie

log = logging.getLogger(__name__)


async def write_movies_to_redis(object_list: list[Movie | Serie]) -> None:
    client = await redis.from_url(settings.REDIS_URL)

    async with client.pipeline(transaction=True) as pipe:
        for idx, obj in enumerate(object_list):
            await pipe.set(idx, obj.json()).execute()


async def read_one_movie_from_redis(idx: int) -> Movie | None:
    try:
        client = await redis.from_url(settings.REDIS_URL)
        movie = await client.get(idx)
        movie = json.loads(movie)
        await client.delete(idx)
        return Movie(**movie)
    except Exception:
        log.exception("Error while reading from redis")
    return None


async def clear_redis() -> None:
    client = await redis.from_url(settings.REDIS_URL)
    await client.flushdb()
