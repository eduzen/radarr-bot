import pytest

from rbot.radarr.api import add_movie_to_radarr, get_movies_from_radarr
from rbot.storage.models import Movie


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=["X-Api-Key"])
@pytest.mark.skip(reason="needs fixing")
async def test_get_movies_from_radarr():
    result = await get_movies_from_radarr()
    assert len(result) >= 379
    assert type(result[0]) == Movie


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=["X-Api-Key"])
async def test_add_movie_already_in_radarr():
    tmbdb_id = 715931  # Emancipation (2022)
    response = await add_movie_to_radarr(tmdb_id=tmbdb_id)
    assert response == "Movie has not been added!"


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=["X-Api-Key"])
@pytest.mark.skip(reason="movie already there")
async def test_add_movie_to_radarr():
    tmbdb_id = 359724  # Ford vs Ferrari (2019)
    response = await add_movie_to_radarr(tmdb_id=tmbdb_id)
    assert response == "Movie has been added!"


@pytest.mark.asyncio
@pytest.mark.vcr(filter_headers=["X-Api-Key"])
async def test_add_movie_to_radarr_error():
    response = await add_movie_to_radarr(tmdb_id="champagne")
    assert response == "Movie has not been added!"
