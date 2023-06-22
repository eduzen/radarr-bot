import logging
import urllib

import httpx
from decouple import config

from rbot.storage.models import (
    Movie,
    Series,
    process_movie_search_result,
    process_movie_search_results,
    process_series_search_results,
)

client = httpx.Client()
log = logging.getLogger(__name__)

TMDB_API_KEY = config("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3/"


async def search_movie(query: str) -> list[Movie]:
    query_params_dict = {
        "query": query,
        "api_key": TMDB_API_KEY,
    }

    query_params = urllib.parse.urlencode(query_params_dict)
    TMDB_SEARCH_URL = f"{TMDB_BASE_URL}search/movie?{query_params}"

    response = client.get(TMDB_SEARCH_URL)
    response.raise_for_status()

    movies = await process_movie_search_results(response.json()["results"])
    log.debug(f"Found {len(movies)} movies")
    return movies


async def search_series(query: str) -> list[Series]:
    query_params_dict = {
        "query": query,
        "api_key": TMDB_API_KEY,
        "include_adult": False,
    }

    query_params = urllib.parse.urlencode(query_params_dict)
    TMDB_SEARCH_URL = f"{TMDB_BASE_URL}search/tv?{query_params}"

    response = client.get(TMDB_SEARCH_URL)
    response.raise_for_status()

    movies = await process_series_search_results(response.json()["results"])
    log.debug(f"Found {len(movies)} movies")
    return movies


async def get_movie_detail(movie_id: int) -> Movie | dict:
    query_params_dict = {
        "api_key": TMDB_API_KEY,
    }
    query_params = urllib.parse.urlencode(query_params_dict)

    TMDB_DETAIL_URL = f"{TMDB_BASE_URL}movie/{movie_id}?{query_params}"

    response = client.get(TMDB_DETAIL_URL)

    response.raise_for_status()

    try:
        movie = await process_movie_search_result(response.json())
        return movie
    except Exception:
        log.exception("Movie not found")
    return {}
