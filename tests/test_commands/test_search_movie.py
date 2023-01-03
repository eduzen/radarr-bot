import pytest

from rbot.tmdb.api import search_movie


@pytest.mark.asyncio
async def test_search_movie():
    movie_result = await search_movie("The Matrix")

    for result in movie_result["results"]:
        assert "the matrix" in result["title"].lower()
