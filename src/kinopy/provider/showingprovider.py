from abc import ABC, abstractmethod

import lxml.html

from ..datamodel import Showing


# should stuff in this module do the requests too?
# maybe as base functionality in ShowingProvider?
# don't forget that Coolidge needs to do N requests for N days

class ShowingProvider(ABC):
    @classmethod
    @abstractmethod
    def to_calendar_html(cls) -> str:
        raise NotImplementedError

    # intent is that this isn't used directly, but subclasses are
    # further abstract classes that define some parsing/sourcing thingy
    # that gives you list[Showing]


class ShowingHTMLProvider(ShowingProvider):
    @classmethod
    @abstractmethod
    def from_html(cls, src: lxml.html.Element) -> list[Showing]:
        raise NotImplementedError


class ShowingJSONProvider(ShowingProvider):
    @classmethod
    @abstractmethod
    def from_json(cls, src: str) -> list[Showing]:
        raise NotImplementedError
