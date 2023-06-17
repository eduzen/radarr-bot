import asyncio

import pytest

from rbot.tmdb.api import Series, search_series


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_search_series():
    series_result = await search_series("The Idol")

    for series in series_result:
        assert "idol" in series.title.lower()


@pytest.mark.asyncio
@pytest.mark.vcr(filter_query_parameters=["api_key"])
async def test_search_invalid_serie():
    series_result = await search_series("das12ad9ds3asdd0d8sda")

    assert len(series_result) == 0


@pytest.mark.parametrize("vote_average", ("", None))
def test_series_dataclass_validations(vote_average):
    with pytest.raises(ValueError):
        Series(
            id=603,
            name="The Idol",
            first_air_date="1999-03-31",
            vote_average=vote_average,
            backdrop_path="/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg",
        )


def test_movie_dataclass_year_and_poster():
    serie = Series(
        id=603,
        name="The idol",
        first_air_date="1999-03-31",
        vote_average=8.1,
        backdrop_path="/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg",
    )
    assert serie.vote_average == 8.1
    assert serie.title in str(serie)
    assert f"({serie.year})" in str(serie)
    assert (
        serie.poster
        == "https://image.tmdb.org/t/p/original/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg"
    )
