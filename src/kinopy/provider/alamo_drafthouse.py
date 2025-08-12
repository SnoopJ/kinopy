from __future__ import annotations

import json
from collections import defaultdict
from datetime import date, datetime
from typing import Any

from ..datamodel import CACHE_ROOT, Showing
from ..util import StrEnum, daily_cache, web


CACHE = CACHE_ROOT.joinpath("AlamoDrafthouse")
CACHE.mkdir(exist_ok=True, parents=True)


BOSTON = 2901

class AlamoProvider:
    JSON_URL = "https://drafthouse.com/s/mother/v2/schedule/market/boston"
    PRESENTATION_URL_PATT = "https://drafthouse.com/boston/show/{slug}?cinemaId={cinemaId}"
    # can also add sessionId=… to get a specific showing, not that I expect to use it
    SESSION_URL_PATT = "https://drafthouse.com/boston/show/{slug}?cinemaId={cinemaId}&sessionId={sessionId}"

    Slug = str
    Session = dict[str, Any]
    SessionByPresentation = dict[Slug, list[Session]]

    # TODO: ugh the return types are going to be a bit of a nuisance since different data sources provide different
    # temporal granularity, but maybe mapping-of-mapping is the way to go in general?
    @classmethod
    def from_json(cls, data: dict) -> dict[date, dict[Slug, list[Showing]]]:
        presentation_data = {pres["slug"]: pres for pres in data["data"]["presentations"]}
        sessions_by_date = cls.sessions_by_date(data, presentation_data)

        shows_by_date = defaultdict(lambda: defaultdict(list))

        for dt, ses_by_pres in sessions_by_date.items():
            for slug, sessions in ses_by_pres.items():
                # ASSUME: there's at least one session and they're all in the same cinemaId
                cinemaId = sessions[0]["cinemaId"]
                sessionId = sessions[0]["sessionId"]
                pres = presentation_data[slug]

                title = pres["show"]["title"]
                url = cls.SESSION_URL_PATT.format(slug=slug, cinemaId=cinemaId, sessionId=sessionId)
                excerpt = None

                show = Showing(
                    date=dt,
                    title=title,
                    url=url,
                    excerpt=excerpt,
                )

                if slug in shows_by_date[dt]:
                    raise ValueError("already populated")

                shows_by_date[dt][slug] = show

        return shows_by_date

    @classmethod
    def sessions_by_date(cls, data: dict, presentation_data: dict) -> dict[date, dict[str, list]]:
        result: dict[date, dict[str, list]] = defaultdict(lambda: defaultdict(list))

        for ses in data["data"]["sessions"]:
            slug = ses["presentationSlug"]

            pres = presentation_data[slug]

            start_time = datetime.fromisoformat(ses["showTimeClt"])
            date = start_time.date()

            result[date][slug].append(ses)

        return result

    @classmethod
    @daily_cache(cachedir=CACHE, json=True)
    def showings_json(cls) -> dict:
        response = web.get(cls.JSON_URL)
        response.raise_for_status()

        result = response.json()

        return result
