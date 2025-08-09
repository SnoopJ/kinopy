from __future__ import annotations

import json
import itertools
import sys
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

from kinopy.datamodel import Day, Cinema, Showing, ShowingCalendar
from kinopy.provider import AlamoProvider, CoolidgeCornerProvider, SomervilleTheatreProvider

if sys.version_info < (3, 11):
    import tomli as tomllib
else:
    import tomllib


HERE = Path(__file__).parent
CONFIG_FILE = HERE.joinpath("kinopy.toml")

if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "rb") as f:
        CONFIG = tomllib.load(f)
else:
    CONFIG = {}


def showings_by_cinema() -> dict[Cinema, dict[Day, Showing]]:
    results = {}

    today = date.today()
    nextweek = today + timedelta(days=7)

    # ALAMO
    alamo_src = AlamoProvider.showings_json()
    alamo_presentations = AlamoProvider.from_json(alamo_src)
    alamo_filtered = {dt.day: sorted((show for slug,show in pres.items()), key=lambda show: show.title) for dt, pres in alamo_presentations.items() if dt < nextweek}
    # NOTE: the sort here gives a nice ordering on the page for presentations showing on multiple days
    # TODO: handle month boundary
    results["Alamo Drafthouse"] = alamo_filtered

    # COOLIDGE
    # Implement the rest of the owl
    dates = [today+timedelta(days=n) for n in range(7)]
    coolidge_presentations = CoolidgeCornerProvider.showings_for_dates(dates=dates)
    results["Coolidge Corner Theatre"] = {dt.day: sorted(shows, key=lambda s: s.title) for dt, shows in coolidge_presentations.items()}

    # SOMERVILLE
    token = CONFIG.get("kinopy", {}).get("provider", {}).get("somerville_theatre", {}).get("token")
    if token:
        somerville_presentations = SomervilleTheatreProvider(veezi_token=token).showings_by_date()
        results["Somerville Theatre"] = {dt.day: sorted(shows, key=lambda s: s.title) for dt, shows in somerville_presentations.items() if dt in dates}
    else:
        print("No access token for Somerville Theatre, skipping")

    return results


def main():
    shows = showings_by_cinema()

    # Showtime!
    cal = ShowingCalendar(shows)

    cal_table = cal.formatweek()

    cinema_checkboxes = "\n".join(f'<input type="checkbox" checked=on onClick="toggleCinema(\'{cinema.replace(" ", "-")}\')">{cinema.title()}</input> <br/>' for cinema in shows.keys())
    show_titles = set(show.title for showlst in itertools.chain.from_iterable(cinema.values() for cinema in shows.values()) for show in showlst)
    title_checkboxes = "\n".join(f'<input type="checkbox" checked=on onClick="toggleMovie(\'{title}\')">{title}</input> <br/>' for title in sorted(show_titles))

    html = dedent(
        f"""
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <title>Movie showings in selected theatres in the Boston metro area</title>
            <link type="text/css" rel="stylesheet" href="cal.css" />
            <script src="cal.js"></script>
        </head>
        <body>
            {cal_table}

            <hr/>
            {cinema_checkboxes}
            <div class="title-filters">
                {title_checkboxes}
            </div>

        </body>
        </html>
        """
    )

    Path("cal.html").write_text(html)


if __name__ == "__main__":
    main()
