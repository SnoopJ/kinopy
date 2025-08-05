from calendar import HTMLCalendar
from textwrap import dedent


# TODO: need some way to render just one week at a time, since vertical
# space is at a serious premium

class ShowingCalendar(HTMLCalendar):
    """
    For generating calendars of showings
    """
    cssclasses_weekday_head = [cls + "-head" for cls in HTMLCalendar.cssclasses]

    def __init__(self, shows):
        self._shows = shows
        super().__init__()

    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        if day == 0:
            # day outside month
            return '<td class="%s">&nbsp;</td>' % self.cssclass_noday
        else:
            wd = self.cssclasses[weekday]
            shows_txt = "\n".join(f'<li><a href="{show.url}"><i>{show.title}</i></a></li>' for show in self._shows.get(day, []))

            # TODO: eventually I would like to have several <ul>, inside of <div> I guess,
            # segregating showings by the cinema (provider)
            return dedent(
                f'''
                <td class="{wd}">
                    <ul>
                        {shows_txt}
                    </ul>
                </td>
                '''
            )
