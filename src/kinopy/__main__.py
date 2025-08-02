import time
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent, indent, wrap
from typing import Iterable

import lxml.html
import requests

from .calendar import MovieCalendar
from .showing import Showing
from .provider import URL_BASE


HERE = Path(__file__).parent
CACHE = HERE.joinpath("cache")
CACHE.mkdir(exist_ok=True)

REQUEST_DT = 0.5  # in seconds


def scrape_showings_page(dt: date, use_cache: bool = True) -> bytes:
    stamp = dt.isoformat()
    fn = CACHE.joinpath(f"{stamp}.html")

    if use_cache and fn.exists():  # TODO: cache invalidation
        return fn.read_bytes()

    url = f"{URL_BASE}/showtimes?date={stamp}"
    response = requests.get(url, allow_redirects=True)
    response.raise_for_status()

    fn.write_bytes(response.content)

    time.sleep(REQUEST_DT)  # TODO: do something less inelegant

    return response.content


def main():
    # TODO: deal with spans that cross month boundaries
    # for now, let's just assume the next week is inside this month
    DAYS = 28
    today = date.today()

    showings = []

    for dt in (today + timedelta(days=n) for n in range(DAYS+1)):
        page = scrape_showings_page(dt)

        try:
            tree = lxml.html.fromstring(page)
            for film_card in tree.xpath("//div[@class='film-card']"):
                show = Showing.from_card_html(film_card, date=dt)
                showings.append(show)
        except Exception as exc:
            print(f"Failed to parse shows for {dt}. Exception was:")
            print(indent(repr(exc), prefix="\t> "))
            CACHE.joinpath(f"{dt.isoformat()}.html").touch()  # TODO: kludge to keep from hitting the site again and again

    cal = MovieCalendar(showings=showings)
    table = cal.formatmonth(today.year, today.month)

    html = dedent(
        f"""
        <html>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <head>
            <link type="text/css" rel="stylesheet" href="cal.css" />
        </head>
        <body>
        {table}
        </body>
        </html>
        """
    )

    with open("/home/snoopjedi/www/files/cal.html", "w") as f:
        f.write(html)


if __name__ == "__main__":
    main()
