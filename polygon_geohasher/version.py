from typing import Union


def _safe_int(string: str) -> Union[int, str]:
    try:
        return int(string)
    except ValueError:
        return string


__version__ = "0.0.1"
VERSION = tuple(_safe_int(x) for x in __version__.split("."))
