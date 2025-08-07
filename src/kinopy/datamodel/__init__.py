from pathlib import Path

from .showingcalendar import ShowingCalendar
from .showing import Showing
from .types_ import Day, Cinema


CACHE_ROOT = Path().joinpath("kinopy_cache")
CACHE_ROOT.mkdir(exist_ok=True, parents=True)
