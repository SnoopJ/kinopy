import json
from datetime import date, timedelta
from pathlib import Path
from textwrap import dedent

from kinopy.datamodel import ShowingCalendar
from kinopy.provider import AlamoProvider


HERE = Path(__file__).parent

if __name__ == "__main__":
    src = HERE.joinpath("example_data", "alamo.json").read_text()
    presentations = AlamoProvider.from_json(src)
    mindate = min(presentations.keys())
    nextmonth = date(year=mindate.year, month=mindate.month+1, day=1)

    filtered_shows = {dt.day: [show for slug,show in pres.items()] for dt, pres in presentations.items() if dt < nextmonth}

    cal = ShowingCalendar(filtered_shows)


    cal_table = cal.formatmonth(mindate.year, mindate.month)

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

    Path("out.html").write_text(html)
