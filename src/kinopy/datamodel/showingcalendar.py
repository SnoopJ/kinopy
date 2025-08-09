from calendar import HTMLCalendar
from datetime import date, timedelta
from textwrap import dedent
from typing import Any, Optional

from .types_ import Day, Cinema
from .showing import Showing


class ShowingCalendar(HTMLCalendar):
    """
    For generating calendars of showings
    """
    cssclasses_weekday_head = [cls + "-head" for cls in HTMLCalendar.cssclasses]

    Slug = str

    # NOTE: this signature does not allow for multiple days with the same number across month boundaries but I'm not
    # sure it matters since I'm pretty rapidly orienting around using weeks and weeks do not have this problem
    def __init__(self, shows: dict[Day, Showing]):
        self._shows = shows
        super().__init__()

    def formatday(self, day, weekday) -> str:
        """
        Return a day as a table cell.
        """
        if day == 0:
            # day outside month
            return '<td class="%s">&nbsp;</td>' % self.cssclass_noday
        else:
            showing_sets = []

            wd = self.cssclasses[weekday]
            for cinema, shows in self._shows.items():
                shows_txt = "\n".join(f'<li><a href="{show.url}"><i>{show.title}</i></a></li>' for show in shows.get(day, []))

                showing_sets.append(
                    dedent(
                        f'''
                        <div class="cinema-root {cinema.lower().replace(' ', '-')}">
                            <span>{cinema}</span>
                            <ul>
                                {shows_txt}
                            </ul>
                        </div>
                        '''
                    )
                )

            cell_txt = "\n<hr/>\n".join(showing_sets)

            result = dedent(
                f'''
                <td class="{wd}">
                    {cell_txt}
                </td>
                '''
            )

            return result

    def formatweek(self, starting_day: Optional[date] = None) -> str:
        if starting_day is None:
            starting_day = date.today()

        MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        mon_start = MONTHS[starting_day.month - 1]
        mon_end = MONTHS[(starting_day + timedelta(days=5)).month - 1]

        week = []
        for n in range(7):
            d = starting_day + timedelta(days=n)
            week.append((d.day, d.weekday()))

        daytxt = '\n'.join(f'<th class="daynum">{self.cssclasses[wd].title()} {day}</th>' for (day, wd) in week)
        cal_table = super().formatweek(week)

        html = dedent(
            f"""
            <table>
                <thead>
                    <th colspan=7>
                        <h3>{mon_start} {week[0][0]} - {mon_end} {week[-1][0]}</h3>
                    </th>
                </thead>
                <thead>
                    {daytxt}
                </thead>
                {cal_table}
            </table>
            """
        )

        return html
