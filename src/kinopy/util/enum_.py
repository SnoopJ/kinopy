import sys

if sys.version_info < (3, 11):
    from backports_strenum import StrEnum
else:
    from enum import StrEnum


__all__ = [
    "StrEnum"
]
