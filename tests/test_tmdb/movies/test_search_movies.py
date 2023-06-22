import asyncio

import pytest

from rbot.tmdb.api import get_movie_detail, search_movie


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_get_movie_detail():
    movie = await get_movie_detail(movie_id=79026)
    movie.title == "El padrino: The Latin Godfather (2004)"


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_search_movie():
    movies_result = await search_movie("The Matrix")

    for movie in movies_result:
        assert "matrix" in movie.title.lower()


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_search_invalid_movie():
    movie_result = await search_movie("das12ad9ds3asdd0d8sda")

    assert len(movie_result) == 0
