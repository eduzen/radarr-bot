import pytest

from rbot.models import Movie
from rbot.radarr.api import get_movies_from_radarr

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
