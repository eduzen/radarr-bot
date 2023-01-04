import datetime
import urllib
from dataclasses import dataclass
from typing import Any

import httpx
from decouple import config

client = httpx.Client()
TMDB_API_KEY = config("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3/"


@dataclass
class Movie:
    title: str
    release_date: str
    backdrop_path: str
    vote_average: int

    @property
    def year(self) -> int:
        date = datetime.datetime.strptime(self.release_date, "%Y-%m-%d")
        return date.year

    @property
    def poster(self) -> str:
        return f"http://image.tmdb.org/t/p/original{self.backdrop_path}"


async def process_movie_search_result(result: dict[str, Any]) -> Movie:
    movie = Movie(
        title=result["title"],
        release_date=result["release_date"],
        vote_average=result["vote_average"],
        backdrop_path=result["backdrop_path"],
    )
    return movie


async def process_movie_search_results(
    search_results: list[dict[Any, Any]]
) -> list[Movie]:
    movies = []
    for result in search_results:
        movie = await process_movie_search_result(result)
        movies.append(movie)
    return movies


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

    return movies


async def get_movie_detail(movie_id: int) -> Movie:
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
    except Exception as e:
        print("Movie not found", e)
    return {}
