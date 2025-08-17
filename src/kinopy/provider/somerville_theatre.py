import json
from collections import defaultdict
from datetime import date, datetime
from functools import cache
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_showings_cache, web


CACHE = CACHE_ROOT.joinpath("SomervilleTheatre")
CACHE.mkdir(exist_ok=True, parents=True)


class SomervilleTheatreProvider:
    JSON_URL = "https://api.us.veezi.com/v1/websession"
    PRODUCTION_URL_PATTERN = "https://www.somervilletheatre.com/production/{slug}/"

    class Config(BaseSettings):
        token: Optional[SecretStr] = Field(default=None, example="<Somerville Theatre Veezi token>")

    def __init__(self, kinopy_config: BaseSettings):
        if kinopy_config.provider is None:
            raise ValueError("Veezi token not available")

        config = kinopy_config.provider.somerville_theatre

        if config is None or config.token is None:
            raise ValueError("Veezi token not available")

        self._token = config.token

    @classmethod
    @cache
    def film_page_url(cls, title: str) -> Optional[str]:
        """
        Try to provide a URL to a 'nice' film page

        The URL provided by Veezi's API goes directly to the ticket purchase page,
        but Somerville Theatre provides a film summary page that would be preferable.
        Sometimes the Somerville Theatre page has a different 'slug' and sometimes there
        is no page at all, so we have to be a bit careful.

        It seems that replacing spaces with '-' in the film titles mostly Just Works™
        to guess the Somerville Theatre URL, but we'll send a HEAD just to be sure and
        fall back on the URL provided by Veezi if necessary
        """
        slug = title.strip().replace(" ", "-")
        theatre_url = cls.PRODUCTION_URL_PATTERN.format(slug=slug)
        response = web.head(theatre_url)

        if response.ok:
            result = theatre_url
        else:
            result = None

        return result


    @daily_showings_cache(cachedir=CACHE)
    def showings_by_date(self, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        result = defaultdict(list)
        data = self.showings_json()

        seen = set()

        for pres in data:
            # NOTE: crude approach, but effective
            film_id = pres["FilmId"]
            title = pres["Title"]
            dt = datetime.fromisoformat(pres["FeatureStartTime"]).date()
            if (dt, film_id) in seen:
                print(f"Seen title already, skipping: {title!r}")
                continue

            seen.add((dt, film_id))
            if film_page_url := self.film_page_url(title):
                url = film_page_url
            else:
                url = pres["Url"]

            excerpt = None

            show = Showing(
                date=str(dt),
                title=title,
                url=url,
                excerpt=excerpt,
            )

            result[dt].append(show)

        result = {dt: sorted(shows, key=lambda s: s.title) for dt, shows in result.items() if from_date <= dt <= to_date}

        return result


    def showings_json(self) -> dict:
        headers = {"VeeziAccessToken": self._token.get_secret_value()}
        response = web.get(self.JSON_URL, headers=headers)
        response.raise_for_status()

        result = response.json()

        return result
