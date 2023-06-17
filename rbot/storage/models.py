import datetime
import logging
from typing import Any

from pydantic import BaseModel

log = logging.getLogger(__name__)


class Movie(BaseModel):
    id: int | None
    tmdbId: int | None
    title: str
    release_date: str | None
    backdrop_path: str | None
    poster_path: str | None
    vote_average: float | None
    poster: str | bytes
    year: int | str | None
    ratings: dict[str, dict[str, Any]] | None

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        self.poster = self.build_poster_url()
        self.year = self.build_year()
        self.vote_average = self.build_vote_average()

    def __str__(self) -> str:
        return f"{self.title} ({self.year})\nRating: {self.rating}\nLink: {self.link}"

    @property
    def imdb_rating(self) -> float:
        try:
            value = self.ratings["imdb"]["value"]  # type: ignore
        except KeyError:
            return 0.0
        return value

    @property
    def alternative_rating(self) -> float:
        if not self.vote_average:
            return 0.0
        try:
            value = round(self.vote_average, 1)
        except KeyError:
            return 0.0
        return value

    def build_vote_average(self) -> float:
        if not self.vote_average and not self.ratings:
            raise ValueError("vote_average is required")

        if self.ratings:
            return self.imdb_rating

        if self.vote_average:
            return self.alternative_rating

        return 0.0

    def build_year(self) -> int | str:
        if self.year:
            return self.year

        if self.release_date:
            date = datetime.datetime.strptime(self.release_date, "%Y-%m-%d")
            return date.year

        raise ValueError("Release date or year is required")

    @property
    def rating(self) -> str:
        if not self.vote_average:
            return "N/A"
        return f"{round(self.vote_average, 1)}/10"

    def build_poster_url(self) -> str:
        if self.poster_path is None and self.backdrop_path is None:
            return "https://image.tmdb.org/"
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/original{self.poster_path}"
        return f"https://image.tmdb.org/t/p/original{self.backdrop_path}"

    @property
    def link(self) -> str:
        return f"https://www.themoviedb.org/movie/{self.id}"


class Series(BaseModel):
    id: int | None
    tmdbId: int | None
    name: str
    first_air_date: str | None
    backdrop_path: str | None
    poster_path: str | None
    vote_average: float | None
    poster: str
    ratings: dict[str, dict[str, Any]] | None
    vote_count: int | None
    year: int | str | None

    def __init__(self, **data: dict[str, Any]) -> None:
        super().__init__(**data)
        self.poster = self.build_poster_url()
        self.vote_average = self.build_vote_average()
        self.year = self.build_year()

    def __str__(self) -> str:
        return (
            f"{self.name} ({self.year})\nRating: {self.vote_count}\nLink: {self.link}"
        )

    @property
    def title(self) -> str:
        return self.name

    @property
    def imdb_rating(self) -> float:
        try:
            value = self.ratings["imdb"]["value"]  # type: ignore
        except KeyError:
            return 0.0
        return value

    @property
    def alternative_rating(self) -> float:
        if not self.vote_average:
            return 0.0
        try:
            value = round(self.vote_average, 1)
        except KeyError:
            return 0.0
        return value

    def build_vote_average(self) -> float:
        if not self.vote_average and not self.ratings:
            raise ValueError("vote_average is required")

        if self.ratings:
            return self.imdb_rating

        if self.vote_average:
            return self.alternative_rating

        return 0.0

    def build_year(self) -> int | str:
        if self.year:
            return self.year

        if self.first_air_date:
            date = datetime.datetime.strptime(self.first_air_date, "%Y-%m-%d")
            return date.year

        raise ValueError("Release date or year is required")

    @property
    def rating(self) -> str:
        if not self.vote_average:
            return "N/A"
        return f"{round(self.vote_average, 1)}/10"

    def build_poster_url(self) -> str:
        if self.poster_path is None and self.backdrop_path is None:
            return "https://image.tmdb.org/"
        if self.poster_path:
            return f"https://image.tmdb.org/t/p/original{self.poster_path}"
        return f"https://image.tmdb.org/t/p/original{self.backdrop_path}"

    @property
    def link(self) -> str:
        return f"https://www.themoviedb.org/tv/{self.id}"


async def process_movie_search_result(result: dict[str, Any]) -> Movie:
    movie = Movie(**result)
    return movie


async def process_movie_search_results(
    search_results: list[dict[Any, Any]]
) -> list[Movie]:
    movies = []
    for result in search_results:
        try:
            movie = await process_movie_search_result(result)
            movies.append(movie)
        except ValueError as e:
            log.error("Not valid movie... skipping it: %s", e)
    return movies


async def process_serie_search_result(result: dict[str, Any]) -> Series:
    log.info("### Processing series: %s", result)
    series = Series(**result)
    return series


async def process_serie_search_results(
    search_results: list[dict[Any, Any]]
) -> list[Series]:
    list_of_series = []
    for result in search_results:
        try:
            series = await process_serie_search_result(result)
            list_of_series.append(series)
        except ValueError as e:
            log.error("Not valid series... skipping it: %s", e)
    return list_of_series
