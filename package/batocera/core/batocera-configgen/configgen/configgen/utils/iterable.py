from __future__ import annotations

from typing import TYPE_CHECKING, Any, overload

if TYPE_CHECKING:
    from collections.abc import Iterable


@overload
def first[T](iterable: Iterable[T], default: None = ...) -> T | None:
    ...


@overload
def first[T, V](iterable: Iterable[T], default: V) -> T | V:
    ...


def first(iterable: Iterable[Any], default: Any = None) -> Any:
    for item in iterable:
        return item

    return default
