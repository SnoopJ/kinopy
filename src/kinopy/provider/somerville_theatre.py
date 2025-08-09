import json
from collections import defaultdict
from datetime import date, datetime

import requests

from ..datamodel import CACHE_ROOT, Showing


CACHE = CACHE_ROOT.joinpath("SomervilleTheatre")
CACHE.mkdir(exist_ok=True, parents=True)


class SomervilleTheatreProvider:
    JSON_URL = "https://api.us.veezi.com/v1/websession"

    def __init__(self, veezi_token: str):
        self._token = veezi_token

    @classmethod
    def showings_by_date(cls) -> dict[date, list[Showing]]:
        result = defaultdict(list)
        data = cls.showings_json()

        seen = set()

        for pres in data:
            # NOTE: crude approach, but effective
            film_id = pres["FilmId"]
            if film_id in seen:
                continue
            seen.add(film_id)

            dt = datetime.fromisoformat(pres["FeatureStartTime"]).date()
            title = pres["Title"]
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


    @classmethod
    def showings_json(cls) -> dict:
        fn = CACHE.joinpath(f"{date.today().isoformat()}.json")
        if fn.exists():
            result = json.loads(fn.read_text())
        else:
            headers = {"VeeziAccessToken": self._token}
            response = requests.get(cls.JSON_URL, headers=headers)
            response.raise_for_status()

            result = response.json()

            fn.write_text(json.dumps(result))

        return result
