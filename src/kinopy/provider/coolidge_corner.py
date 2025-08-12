import time
from datetime import date, timedelta

import lxml.html

from ..datamodel import CACHE_ROOT, Showing
from ..util import daily_showings_cache, web


CACHE = CACHE_ROOT.joinpath("CoolidgeCorner")
CACHE.mkdir(exist_ok=True, parents=True)


class CoolidgeCornerProvider:
    QUERY_PATTERN = "https://coolidge.org/showtimes?date={isoformat}"

    @classmethod
    def from_html(cls, date: date, film_card: lxml.html.Element) -> Showing:
        [link] = film_card.xpath(".//h2/a[@class='film-card__link']")
        rel_url = link.attrib["href"]
        url = f"https://coolidge.org/{rel_url}"
        title = link.text_content()

        [excerpt_tag] = film_card.xpath(".//div[@class='film-card__excerpt']")
        excerpt = excerpt_tag.text_content()

        return Showing(
            date=str(date),
            title=title,
            url=url,
            excerpt=excerpt,
        )

    @classmethod
    def from_showing_page(cls, date: date, page_src: str) -> list[Showing]:
        html = lxml.html.fromstring(page_src)

        film_cards = html.xpath("//div[@class='film-card']")

        result = [cls.from_html(date, fc) for fc in film_cards]
        return result

    @classmethod
    @daily_showings_cache(cachedir=CACHE)
    def showings_by_date(cls, from_date: date, to_date: date) -> dict[date, list[Showing]]:
        ndays = (to_date - from_date).days
        dates = [from_date + timedelta(days=n) for n in range(ndays+1)]

        return cls.showings_for_dates(dates)

    @classmethod
    def showings_for_dates(cls, dates: list[date]) -> dict[date, list[Showing]]:
        result = {}

        for d in dates:
            url = cls.QUERY_PATTERN.format(isoformat=d.isoformat())
            response = web.get(url)
            response.raise_for_status()
            src = response.content

            # TODO: more sophisticated rate limiting
            time.sleep(0.25)

            shows = cls.from_showing_page(date=d, page_src=src)
            result[d] = shows

        result = {dt: sorted(shows, key=lambda s: s.title) for dt, shows in result.items() if dt in dates}

        return result
