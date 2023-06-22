import pytest

from rbot.storage.models import Movie


@pytest.mark.parametrize("vote_average", ("", None))
def test_movie_dataclass_validations(vote_average):
    with pytest.raises(ValueError):
        Movie(
            id=603,
            title="The Matrix",
            release_date="1999-03-31",
            vote_average=vote_average,
            backdrop_path="/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg",
        )


def test_movie_dataclass_year_and_poster():
    movie = Movie(
        id=603,
        title="The Matrix",
        release_date="1999-03-31",
        vote_average=8.1,
        backdrop_path="/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg",
    )
    assert movie.vote_average == 8.1
    assert movie.title in str(movie)
    assert f"({movie.year})" in str(movie)
    assert (
        movie.poster
        == "https://image.tmdb.org/t/p/original/hEpWvX6Bp79e.l0qAid8z0JFfMG.jpg"
    )
