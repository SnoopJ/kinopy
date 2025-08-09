import json
from collections import defaultdict
from datetime import date, datetime
from functools import cache
from typing import Optional

from ..datamodel import CACHE_ROOT, Showing
from ..util import web


CACHE = CACHE_ROOT.joinpath("SomervilleTheatre")
CACHE.mkdir(exist_ok=True, parents=True)


class SomervilleTheatreProvider:
    JSON_URL = "https://api.us.veezi.com/v1/websession"
    PRODUCTION_URL_PATTERN = "https://www.somervilletheatre.com/production/{slug}/"

    def __init__(self, veezi_token: str):
        self._token = veezi_token

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


    def showings_by_date(self) -> dict[date, list[Showing]]:
        result = defaultdict(list)
        data = self.showings_json()

        seen = set()

        for pres in data:
            # NOTE: crude approach, but effective
            film_id = pres["FilmId"]
            if film_id in seen:
                continue
            seen.add(film_id)

            dt = datetime.fromisoformat(pres["FeatureStartTime"]).date()
            title = pres["Title"]
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

        return result


    def showings_json(self) -> dict:
        fn = CACHE.joinpath(f"{date.today().isoformat()}.json")
        if fn.exists():
            result = json.loads(fn.read_text())
        else:
            headers = {"VeeziAccessToken": self._token}
            response = web.get(self.JSON_URL, headers=headers)
            response.raise_for_status()

            result = response.json()

            fn.write_text(json.dumps(result))

        return result
