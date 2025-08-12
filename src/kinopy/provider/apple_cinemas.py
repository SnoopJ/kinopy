import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from functools import wraps
from pathlib import Path
from typing import Optional

# this curl-impersonate wrapper is necessary to get around TLS fingerprinting
import curl_cffi

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_cache

CACHE = CACHE_ROOT.joinpath("AppleCinemas")
CACHE.mkdir(exist_ok=True, parents=True)

# f604d90 corresponds to companyId, which doesn't seem to vary as far as I can tell
# 5fe26a5ff118402f4e00c6cc is the locationId for Cambridge

class AppleCinemasProvider:
    CAMBRIDGE_LOCATION_ID = "5fe26a5ff118402f4e00c6cc"
    MOVIE_URL_PATTERN = "https://www.applecinemas.com/Kiosk/GetLocationonlineMovies/f604d90/{actualMovieId}/{fromTime}/{toTime}"
    SHOWING_URL_PATTERN = f"https://www.applecinemas.com/{{title_slug}}/{CAMBRIDGE_LOCATION_ID}/{{actualMovieId}}"
    ALL_MOVIES_URL = f"https://www.applecinemas.com/Kiosk/GetAllCompanyLocationMovies/f604d90/{CAMBRIDGE_LOCATION_ID}"

    MovieID = str

    @classmethod
    def showings_by_date(cls, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        sched = cls.schedule(from_date=from_date, to_date=to_date)

        results = defaultdict(list)

        seen = set()

        for movID, showings in sched.items():
            for mov in showings:
                for scr in mov["screens"]:
                    for st in scr["showTimes"]:
                        dt = datetime.fromisoformat(st["showTime"]).date()

                        if (dt, movID) in seen:
                            #print(f"Already tracking movie for {dt.isoformat()}: {movID!r}")
                            continue

                        title = mov["movieDisplayName"]

                        title_slug = title.replace(" ", "-")
                        url = cls.SHOWING_URL_PATTERN.format(title_slug=title_slug, actualMovieId=mov["actualMovieId"])

                        excerpt = None

                        s = Showing(
                            date=str(dt),
                            title=title,
                            url=url,
                            excerpt=excerpt,
                        )

                        results[dt].append(s)
                        seen.add((dt, movID))

        return results

    @classmethod
    @daily_cache(cachedir=CACHE, json=True)
    def schedule(cls, from_date: date, to_date: date) -> dict[MovieID, list]:
        all_movies_response = curl_cffi.get(cls.ALL_MOVIES_URL, impersonate="firefox")
        all_movies_response.raise_for_status()
        all_movies_data = all_movies_response.json()

        movies = defaultdict(list)

        for mov in all_movies_data["schedules"]:
            actualMovieId = mov["actualMovieId"]  # lol, nice
            title = mov["movieName"]

            print(f"Finding showtimes for title: {title!r}")
            mov_data = cls.showings_for_movie(actualMovieId, from_date, to_date)
            movies[actualMovieId].extend(m for m in mov_data if m["locationId"] == cls.CAMBRIDGE_LOCATION_ID)

        return movies

    @classmethod
    def showings_for_movie(cls, actualMovieId: str, from_date: date, to_date: date) -> list:
        assert to_date > from_date, "to_date must come after from_date"

        results = []

        retrieval_date = date.today()

        d = from_date
        while d < to_date:
            st_str = d.strftime("%Y-%m-%dT00:00:00.000Z")
            # NOTE: the ending date parameter appears to not matter at all to the remote server, it does not even need to
            # be after the starting date. We'll set this parameter "right" anyway, as a prayer for that messy API's soul.
            ed_str = d.strftime("%Y-%m-%dT23:59:59.000Z")

            url = cls.MOVIE_URL_PATTERN.format(actualMovieId=actualMovieId, fromTime=st_str, toTime=ed_str)

            try:
                movie_response = curl_cffi.get(url, impersonate="firefox")
                movie_response.raise_for_status()

                mov_data = movie_response.json()
                for m in mov_data:
                    m["actualMovieId"] = actualMovieId
            except Exception:
                continue

            if mov_data:
                results.extend(mov_data)

            d += timedelta(days=1)

        return results
