import json
from collections import defaultdict
from datetime import date, datetime
from functools import cache
from typing import Iterable, Optional

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_showings_cache, web


CACHE = CACHE_ROOT.joinpath("LandmarkKendallSquare")
CACHE.mkdir(exist_ok=True, parents=True)


class LandmarkKendallSquareProvider:
    SCHEDULE_URL = "https://www.landmarktheatres.com/api/gatsby-source-boxofficeapi/schedule"
    PRODUCTION_URL_PATTERN = "https://www.landmarktheatres.com/movies/{slug}"
    MOVIES_URL = "https://www.landmarktheatres.com/api/gatsby-source-boxofficeapi/movies"

    FilmID = str

    @classmethod
    @daily_showings_cache(cachedir=CACHE)
    def showings_by_date(cls, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        payload = {
            "theaters": [
                {
                    "id": "X019B",
                    "timeZone": "America/New_York",
                }
            ],
            "from": from_date.isoformat(),
            "to": to_date.isoformat(),
            "nin": [],
            "sin": [],
        }
        sched_response = web.post(cls.SCHEDULE_URL, json=payload)
        sched_response.raise_for_status()

        results = defaultdict(list)

        sched = sched_response.json()["X019B"]["schedule"]

        film_details = cls.film_details(sched.keys())

        for film_id, presentations in sched.items():
            for d, pres in presentations.items():
                film = film_details[film_id]
                title = film["title"]
                excerpt = film["locale"]["synopsis"]
                url = "https://www.landmarktheatres.com"
                #url = pres["data"]["ticketing"]["urls"][0]
                if film_page_url := cls.film_page_url(title, film_id):
                    url = film_page_url
                else:
                    url = pres["data"]["ticketing"][0]["urls"][0]

                show = Showing(
                    date=str(d),
                    title=title,
                    url=url,
                    excerpt=excerpt,
                )

                results[date.fromisoformat(d)].append(show)

        results = {dt: sorted(shows, key=lambda s: s.title) for dt, shows in results.items() if from_date <= dt <= to_date}

        return results

    @classmethod
    def film_details(cls, fids: Iterable[FilmID]) -> dict[FilmID, dict]:
        id_params = "&".join(f"ids={fid}" for fid in fids)
        details_url = cls.MOVIES_URL + "?basic=false&castingLimit=3&" + id_params
        details_response = web.get(details_url)
        details_response.raise_for_status()

        return {filminfo["id"]: filminfo for filminfo in details_response.json()}

    @classmethod
    @cache
    def film_page_url(cls, title: str, film_id: str) -> Optional[str]:
        """
        Try to provide a URL to a 'nice' film page

        The URL provided by the BoxOffice API goes directly to the ticket purchase page,
        but Landmark provides a film summary page that would be preferable.
        """
        normed_title = title.strip().replace(" ", "-")
        slug = f"{film_id}-{normed_title}"

        theatre_url = cls.PRODUCTION_URL_PATTERN.format(slug=slug)
        response = web.head(theatre_url)

        if response.ok:
            result = theatre_url
        else:
            result = None

        return result
