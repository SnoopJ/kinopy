import sys

if sys.version_info < (3, 11):
    from backports.strenum import StrEnum
else:
    from enum import StrEnum


__all__ = [
    "StrEnum"
]
