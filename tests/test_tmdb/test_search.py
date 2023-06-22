import pytest

from rbot.tmdb.api import Movie, search_movie


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_search_movie():
    title = "The Matrix"
    movies = await search_movie(title)

    for movie in movies:
        assert isinstance(movie, Movie)
        movie_title = movie.title.lower()
        assert "matrix" in movie_title
