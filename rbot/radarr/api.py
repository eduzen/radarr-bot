import logging
from typing import Any

import httpx

from rbot.conf import settings
from rbot.models import process_movie_search_results

log = logging.getLogger(__name__)

headers = {"Content-Type": "application/json", "X-Api-Key": settings.RADARR_API_KEY}


async def movie_loookup(tmdb_id: str) -> dict[str, Any]:
    url = f"{settings.RADARR_BASE_URL}movie/lookup/tmdb?tmdbId={tmdb_id}"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            movie_json = response.json()
            return movie_json
    except Exception as e:
        log.exception(e)
        raise Exception("Could not get movies from Radarr") from e


async def add_movie_to_radarr(tmdb_id: str) -> str:
    try:
        movie_json = await movie_loookup(tmdb_id)
        movie_title = f"{movie_json['title'].strip()} ({movie_json['year']})"
    except Exception:
        log.exception("Could not get movie from TMDB")
        return "Movie has not been added!"

    try:
        payload = {
            "title": movie_json["title"],
            "tmdbId": tmdb_id,
            "QualityProfileId": settings.QUALITY_PROFILE_ANY,
            "RootFolderPath": settings.RADARR_ROOT_FOLDER,
            "folder": movie_title,
            "monitored": True,
        }
        url = f"{settings.RADARR_BASE_URL}movie"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return "Movie has been added!"
    except Exception as e:
        log.exception(e)

    return "Movie has not been added!"


async def get_movies_from_radarr() -> bool:
    url = f"{settings.RADARR_BASE_URL}movie"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            movies = await process_movie_search_results(data)
            return movies
    except Exception as e:
        log.exception(e)
        raise Exception("Could not get movies from Radarr") from e
