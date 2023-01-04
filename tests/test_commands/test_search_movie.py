import asyncio

import pytest

from rbot.tmdb.api import Movie, search_movie, get_movie_detail


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_movie_detail():
    movie = await get_movie_detail(movie_id=79026)
    movie.title == "El padrino: The Latin Godfather (2004)"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_search_movie():
    movies_result = await search_movie("The Matrix")

    for movie in movies_result:
        assert "the matrix" in movie.title.lower()

@pytest.mark.asyncio
@pytest.mark.vcr
async def test_search_invalid_movie():
    movie_result = await search_movie("das12ad9ds3asdd0d8sda")

    assert len(movie_result) == 0


def test_movie_dataclass_year_and_poster():
    movie = Movie(
        title="The Matrix",
        release_date="1999-03-31",
        vote_average=8.1,
        backdrop_path="/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg",
    )

    assert type(movie.to_str()) == str
    assert movie.year == 1999
    assert (
        movie.poster
        == "http://image.tmdb.org/t/p/original/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg"
    )
