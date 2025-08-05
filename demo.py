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

    filtered_shows = {dt.day: sorted((show for slug,show in pres.items()), key=lambda show: show.title) for dt, pres in presentations.items() if dt < nextmonth}

    cal = ShowingCalendar(filtered_shows)

    # TODO: render other weeks, lock each week to Monday? definitely shouldn't be relative to today
    today = date.today()
    week = []
    for n in range(6):
        d = today + timedelta(days=n)
        week.append((d.day, d.weekday()))

    cal_table = cal.formatweek(week)

    daytxt = '\n'.join(f'<th class="daynum">{cal.cssclasses[wd].title()} {day}</th>' for (day, wd) in week)

    html = dedent(
        f"""
        <html>
        <head>
            <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
            <link type="text/css" rel="stylesheet" href="cal.css" />
        </head>
        <body>
            <table>
                <thead>
                    <th colspan=6>
                        <h3>Aug {week[0][0]} - {week[-1][0]}</h3>
                    </th>
                </thead>
                <thead>
                    {daytxt}
                </thead>
                {cal_table}
            </table>
        </body>
        </html>
        """
    )

    Path("cal2.html").write_text(html)
