from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, TypeAlias

if TYPE_CHECKING:
    import enum

    class _MISSING_TYPE(enum.Enum):
        MISSING = enum.auto()

        def __eq__(self, other: object) -> Literal[False]:
            ...

        def __bool__(self) -> Literal[False]:
            ...

        def __hash__(self) -> int:
            ...

        def __repr__(self) -> str:
            ...

    MISSING: Final = _MISSING_TYPE.MISSING
    MissingType: TypeAlias = Literal[_MISSING_TYPE.MISSING]
else:
    class _MissingSentinel:
        __slots__ = ()

        def __eq__(self, other: object) -> Literal[False]:
            return False

        def __bool__(self) -> Literal[False]:
            return False

        def __hash__(self) -> int:
            return 0

        def __repr__(self) -> str:
            return '...'

    MissingType: TypeAlias = _MissingSentinel
    MISSING: Final[MissingType] = _MissingSentinel()
