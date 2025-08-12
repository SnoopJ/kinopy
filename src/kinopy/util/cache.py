import dataclasses
import json as jsonlib
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Optional

from ..datamodel import Showing


def _json_cache_filename(cachedir: Path, prefix: Optional[str] = None, dt: Optional[date] = None) -> Path:
    if dt is None:
        dt = date.today()
    prefix = (prefix + "_") if prefix else ""
    fn = cachedir.joinpath(f"{prefix}{dt.isoformat()}.json")
    return fn


def daily_showings_cache(*, cachedir: Path, prefix: Optional[str] = None):
    """
    Cache the results of the wrapped showings-by-date function on a daily basis.
    Subsequent calls on the same day will return the same value.

    Parameters
    ----------
    json - if given, the results of the function and cache files are treated as JSON when (de)serializing
    """
    def deco(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            fn = _json_cache_filename(cachedir=cachedir, prefix=prefix)

            if fn.exists():
                result_serialized = jsonlib.loads(fn.read_text())
                result = {date.fromisoformat(dt_txt): [Showing(**shw) for shw in shows] for dt_txt, shows in result_serialized.items()}
            else:
                result = func(*args, **kwargs)
                result_serialized = {dt.isoformat(): [dataclasses.asdict(shw) for shw in shows] for dt, shows in result.items()}
                fn.write_text(jsonlib.dumps(result_serialized))

            return result

        def clear_cache(dt: Optional[date] = None):
            fn = _json_cache_filename(cachedir=cachedir, prefix=prefix, dt=dt)
            fn.unlink(missing_ok=True)

        func.clear_cache = clear_cache

        return wrapper

    return deco
