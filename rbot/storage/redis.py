import json
import logging

import redis.asyncio as redis

from rbot.conf import settings

from .models import Movie, Series

log = logging.getLogger(__name__)


async def write_movies_to_redis(movies: list[Movie]) -> None:
    client = await redis.from_url(settings.REDIS_URL)

    async with client.pipeline(transaction=True) as pipe:
        for idx, movie in enumerate(movies):
            await pipe.set(idx, movie.json()).execute()


async def read_one_result_from_redis(idx: int) -> Movie | Series | None:
    try:
        client = await redis.from_url(settings.REDIS_URL)
        response = await client.get(idx)
        result = json.loads(response)
        await client.delete(idx)
        log.warning(f"Read from redis: {result}")

        try:
            return Movie(**result)
        except Exception:
            return Series(**result)

    except Exception:
        log.exception("Error while reading from redis")
    return None


async def clear_redis() -> None:
    client = await redis.from_url(settings.REDIS_URL)
    await client.flushdb()
