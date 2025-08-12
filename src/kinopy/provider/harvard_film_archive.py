from collections import defaultdict
from datetime import date, datetime
from itertools import chain

import lxml.html

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_showings_cache, web


CACHE = CACHE_ROOT.joinpath("HarvardFilmArchiveProvider")
CACHE.mkdir(exist_ok=True, parents=True)


class HarvardFilmArchiveProvider:
    CALENDAR_URL_PATTERN = "https://harvardfilmarchive.org/calendar?date_from={date_from}&date_to={date_to}"

    @classmethod
    @daily_showings_cache(cachedir=CACHE)
    def showings_by_date(cls, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        url = cls.CALENDAR_URL_PATTERN.format(date_from=from_date.strftime("%m/%d/%Y"), date_to=to_date.strftime("%m/%d/%Y"))

        response = web.get(url)
        response.raise_for_status()

        results = defaultdict(list)

        doc = lxml.html.fromstring(response.content)
        event_nodes = doc.xpath("//div[contains(concat(' ', @class, ' '), ' event ')]")
        for evt in event_nodes:
            [time_node] = evt.xpath("./div/time")
            [title_node] = evt.xpath(".//*[@class='event__title']")
            [link_node] = evt.xpath(".//a[@class='event__link']")

            dt = datetime.fromisoformat(time_node.attrib["datetime"]).date()
            title = title_node.text_content()
            rel_url = link_node.attrib["href"].removeprefix("/")
            url = f"https://harvardfilmarchive.org/{rel_url}"
            excerpt = None

            s = Showing(
                date=str(dt),
                title=title,
                url=url,
                excerpt=excerpt,
            )

            results[dt].append(s)

        results = {dt: sorted(shows, key=lambda s: s.title) for dt, shows in results.items() if from_date <= dt <= to_date}

        return results
