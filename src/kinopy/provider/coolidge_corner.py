import time
from datetime import date
from pathlib import Path

import lxml.html
import requests

from ..datamodel import CACHE_ROOT, Showing


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

        showtimes = [st.text_content() for st in film_card.xpath(".//span[@class='showtime-ticket__time']")]
        [excerpt_tag] = film_card.xpath(".//div[@class='film-card__excerpt']")
        excerpt = excerpt_tag.text_content()

        return Showing(
            date=date,
            title=title,
            url=url,
            showtimes=showtimes,
            excerpt=excerpt,
        )

    @classmethod
    def from_showing_page(cls, date: date, page_src: str) -> list[Showing]:
        html = lxml.html.fromstring(page_src)

        film_cards = html.xpath("//div[@class='film-card']")

        result = [cls.from_html(date, fc) for fc in film_cards]
        return result

    @classmethod
    def showings_for_dates(cls, dates: list[date]) -> dict[date, list[Showing]]:
        result = {}

        for d in dates:
            fn = CACHE.joinpath(f"{d.isoformat()}.html")
            if fn.exists():
                src = fn.read_text()
            else:
                url = cls.QUERY_PATTERN.format(isoformat=d.isoformat())
                response = requests.get(url)
                response.raise_for_status()
                src = response.content

                fn.write_bytes(src)

                # TODO: more sophisticated rate limiting
                time.sleep(0.25)

            shows = cls.from_showing_page(date=d, page_src=src)
            result[d] = shows

        return result
