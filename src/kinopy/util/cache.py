import json as jsonlib
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Optional


def _json_cache_filename(cachedir: Path, prefix: Optional[str] = None) -> Path:
    today = date.today()
    prefix = (prefix + "_") if prefix else ""
    fn = cachedir.joinpath(f"{prefix}{today.isoformat()}.json")
    return fn


def daily_cache(*, cachedir: Path, prefix: Optional[str] = None, json: bool = False):
    """
    Cache the results of the wrapped function on a daily basis.
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
                result = fn.read_text()
                if json:
                    result = jsonlib.loads(result)
            else:
                result = func(*args, **kwargs)
                if json:
                    fn.write_text(jsonlib.dumps(result))

            return result

        def clear_cache():
            fn = _json_cache_filename(cachedir=cachedir, prefix=prefix)
            fn.unlink(missing_ok=True)

        func.clear_cache = clear_cache

        return wrapper

    return deco
