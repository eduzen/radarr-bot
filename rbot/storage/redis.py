import json
import logging

import redis.asyncio as redis

from rbot.conf import settings

from .models import Movie

log = logging.getLogger(__name__)


async def write_movies_to_redis(movies: list[Movie]) -> None:
    client = await redis.from_url(settings.REDIS_URL)

    async with client.pipeline(transaction=True) as pipe:
        for idx, movie in enumerate(movies):
            await pipe.set(idx, movie.json()).execute()


async def read_one_movie_from_redis(idx: int) -> Movie | None:
    try:
        client = await redis.from_url(settings.REDIS_URL)
        movie = await client.get(idx)
        movie = json.loads(movie)
        yield Movie(**movie)
        await client.delete(idx)
    except Exception:
        log.exception("Error while reading from redis")


async def clear_redis() -> None:
    client = await redis.from_url(settings.REDIS_URL)
    await client.flushdb()
