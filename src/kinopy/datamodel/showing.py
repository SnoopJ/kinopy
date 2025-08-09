from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional


@dataclass
class Showing:
    date: date
    title: str
    url: str

    # NOTE: optional because I feel like Coolidge is the only one that provides it
    # Is excerpt a good enough name for arbitrary descriptive text? Should I generalize to description?
    excerpt: Optional[str]
