from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

from kinopy.datamodel import Day, Cinema, Showing, ShowingCalendar
from kinopy.provider import AlamoProvider, CoolidgeCornerProvider


HERE = Path(__file__).parent

if __name__ == "__main__":
    shows: dict[Cinema, dict[Day, Showing]] = {}

    today = date.today()
    nextweek = today + timedelta(days=7)

    # ALAMO
    alamo_src = AlamoProvider.showings_json()
    alamo_presentations = AlamoProvider.from_json(alamo_src)
    alamo_filtered = {dt.day: sorted((show for slug,show in pres.items()), key=lambda show: show.title) for dt, pres in alamo_presentations.items() if dt < nextweek}
    # NOTE: the sort here gives a nice ordering on the page for presentations showing on multiple days
    # TODO: handle month boundary
    shows["Alamo Drafthouse"] = alamo_filtered

    # COOLIDGE
    # Implement the rest of the owl
    dates = [today+timedelta(days=n) for n in range(7)]
    coolidge_presentations = CoolidgeCornerProvider.showings_for_dates(dates=dates)
    shows["Coolidge Corner Theatre"] = {dt.day: sorted(shows, key=lambda s: s.title) for dt, shows in coolidge_presentations.items()}

    # Showtime!
    cal = ShowingCalendar(shows)

    cal_table = cal.formatweek()

    html = dedent(
        f"""
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <link type="text/css" rel="stylesheet" href="cal.css" />
        </head>
        <body>
            {cal_table}
        </body>
        </html>
        """
    )

    Path("cal.html").write_text(html)
