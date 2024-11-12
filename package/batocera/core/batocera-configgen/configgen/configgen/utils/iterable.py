from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, overload

if TYPE_CHECKING:
    from collections.abc import Iterable

_T = TypeVar('_T')
_V = TypeVar('_V')


@overload
def first(iterable: Iterable[_T], default: None = ...) -> _T | None:
    ...


@overload
def first(iterable: Iterable[_T], default: _V) -> _T | _V:
    ...


def first(iterable: Iterable[Any], default: Any = None) -> Any:
    for item in iterable:
        return item

    return default
