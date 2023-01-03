import urllib
from typing import Any

import httpx
from decouple import config

client = httpx.AsyncClient()
TMDB_API_KEY = config("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3/"


async def process_movie_search_results(
    search_results: list[dict[Any, Any]]
) -> list[dict[Any, Any]]:
    movies = []
    for result in search_results:
        movie = {}
        movie["title"] = result["title"]
        movie["year"] = result["year"]
        movie["imdb_link"] = result["imdb_link"]

        response = client.get(result["poster_url"])
        if response.status == 200:
            movie["poster"] = await response.read()

        movies.append(movie)
    return movies


async def search_movie(query: str) -> dict[Any, Any]:
    query_params_dict = {
        "query": query,
        "api_key": TMDB_API_KEY,
    }
    query_params = urllib.parse.urlencode(query_params_dict)
    TMDB_SEARCH_URL = f"{TMDB_BASE_URL}search/movie?{query_params}"

    response = await client.get(TMDB_SEARCH_URL)

    response.raise_for_status()

    return response.json()


async def get_movie_detail(movie_id: int) -> dict[Any, Any]:
    query_params_dict = {
        "api_key": TMDB_API_KEY,
    }
    query_params = urllib.parse.urlencode(query_params_dict)

    TMDB_DETAIL_URL = f"{TMDB_BASE_URL}/movie/{movie_id}/?{query_params}"

    response = await client.get(TMDB_DETAIL_URL)

    response.raise_for_status()

    return response.json()
