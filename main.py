from __future__ import annotations

import json
import itertools
import sys
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

from kinopy.datamodel import Day, Cinema, Showing, ShowingCalendar
from kinopy.provider import (
    AlamoProvider,
    AppleCinemasProvider,
    BrattleProvider,
    CoolidgeCornerProvider,
    LandmarkKendallSquareProvider,
    RegentTheatreProvider,
    SomervilleTheatreProvider,
)

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

    from_date = date.today()
    to_date = from_date + timedelta(days=6)

    # SOMERVILLE
    token = CONFIG.get("kinopy", {}).get("provider", {}).get("somerville_theatre", {}).get("token")
    if token:
        print("=== Fetching showings for: Somerville Theatre")
        somerville_presentations = SomervilleTheatreProvider(veezi_token=token).showings_by_date(from_date=from_date, to_date=to_date)
        results["Somerville Theatre"] = somerville_presentations
    else:
        print("=== No access token for Somerville Theatre, skipping")

    # THE BRATTLE
    print("=== Fetching showings for: The Brattle")
    brattle_presentations = BrattleProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["The Brattle"] = brattle_presentations

    # REGENT
    print("=== Fetching showings for: Regent Theatre")
    regent_presentations = RegentTheatreProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["Regent Theatre"] = regent_presentations

    # COOLIDGE
    print("=== Fetching showings for: Coolidge Corner")
    coolidge_presentations = CoolidgeCornerProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["Coolidge Corner Theatre"] = coolidge_presentations

    # ALAMO
    # TODO: handle month boundary
    print("=== Fetching showings for: Alamo Drafthouse")
    alamo_presentations = AlamoProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["Alamo Drafthouse"] = alamo_presentations

    # LANDMARK KENDALL
    print("=== Fetching showings for: Landmark Kendall Square Cinema")
    landmark_presentations = LandmarkKendallSquareProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["Landmark Kendall Square Cinema"] = landmark_presentations

    # APPLE CINEMAS CAMBRIDGE
    print("=== Fetching showings for: Apple Cinemas")
    apple_presentations = AppleCinemasProvider().showings_by_date(from_date=from_date, to_date=to_date)
    results["Apple Cinemas"] = apple_presentations

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
