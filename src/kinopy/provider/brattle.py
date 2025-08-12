import time
from collections import defaultdict
from datetime import date

import lxml.html

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_cache, web


CACHE = CACHE_ROOT.joinpath("Brattle")
CACHE.mkdir(exist_ok=True, parents=True)


class BrattleProvider:
    QUERY_URL = "https://brattlefilm.org/coming-soon/"

    @classmethod
    @daily_cache(cachedir=CACHE, json=True)
    def showings_by_date(cls) -> dict[date, list[Showing]]:
        today = date.today()
        response = web.get(cls.QUERY_URL)
        response.raise_for_status()
        src = response.content

        return cls.shows_from_html(src)

    @classmethod
    def shows_from_html(cls, html: bytes) -> dict[date, list[Showing]]:
        results = defaultdict(list)

        doc = lxml.html.fromstring(html)
        shows = doc.xpath("//div[@class='show-details']")

        for shw in shows:
            [link] = shw.xpath(".//a[@class='title']")
            title = link.text_content().strip()
            url = link.attrib["href"]
            if "/movies/" not in url:
                # special case: non-movie events show up on this page too, and while it's cool that they show up here,
                # they aren't movies and don't seem to be often related to movies, so let's filter those out
                continue

            excerpt = None

            date_children = shw.xpath(".//div[contains(@class, 'date-selector')]//li[@data-date]")

            if not date_children:
                # special case: some Brattle showings do not have any showtimes listed at all
                continue

            dates = set(date.fromtimestamp(int(node.attrib["data-date"])) for node in date_children)
            for d in dates:
                s = Showing(
                    date=d,
                    title=title,
                    url=url,
                    excerpt=excerpt,
                )
                results[d].append(s)

        return results
