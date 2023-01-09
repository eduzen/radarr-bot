import logging

import httpx
from decouple import config

from ..models import process_movie_search_results

# client = httpx.Client()
client = httpx.AsyncClient()
log = logging.getLogger(__name__)
RADARR_API_KEY = config("RADARR_API_KEY")
RADARR_BASE_URL = "http://radarr.huis/api/v3/"

log = logging.getLogger(__name__)


async def add_movie_to_radarr(imdb_id: str) -> bool:
    headers = {"Content-Type": "application/json", "X-Api-Key": RADARR_API_KEY}
    payload = {"movie": {"tmdbId": imdb_id}}
    url = f"{RADARR_BASE_URL}movie"
    async with client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code == 201:
            return True
    return False


async def get_movies_from_radarr() -> bool:
    headers = {"Content-Type": "application/json", "X-Api-Key": RADARR_API_KEY}
    url = f"{RADARR_BASE_URL}movie"
    async with client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        movies = await process_movie_search_results(data)
        return movies
