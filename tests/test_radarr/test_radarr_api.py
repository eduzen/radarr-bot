import pytest

from rbot.models import Movie
from rbot.radarr.api import add_movie_to_radarr, get_movies_from_radarr

# @pytest.mark.asyncio
# @pytest.mark.record
# async def test_add_movie_to_radarr():
#     # Set up environment variables for the test
#     os.environ['RADARR_URL'] = 'http://localhost:7878'
#     os.environ['RADARR_API_KEY'] = 'abc123'

#     # Call the function and check the return value
#     result = await add_movie_to_radarr('tt1234567')
#     assert result == True

#     # Check that the correct request was made
#     assert len(recorder.requests) == 1
#     request = recorder.requests[0]
#     assert request.method == 'POST'
#     assert request.url == 'http://localhost:7878/api/movie'
#     assert request.headers['Content-Type'] == 'application/json'
#     assert request.headers['X-Api-Key'] == 'abc123'
#     assert request.json() == {'movie': {'tmdbId': 'tt1234567'}}


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_get_movies_from_radarr():
    result = await get_movies_from_radarr()
    assert len(result) == 373
    assert type(result[0]) == Movie


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_add_movie_already_in_radarr():
    tmbdb_id = 715931  # Emancipation (2022)
    response = await add_movie_to_radarr(tmdb_id=tmbdb_id)
    assert response == "Movie has not been added!"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_add_movie_to_radarr():
    tmbdb_id = 359724  # Ford vs Ferrari (2019)
    response = await add_movie_to_radarr(tmdb_id=tmbdb_id)
    assert response == "Movie has been added!"


@pytest.mark.asyncio
@pytest.mark.vcr
async def test_add_movie_to_radarr_error():
    response = await add_movie_to_radarr(tmdb_id="champagne")
    assert response == "Movie has not been added!"
