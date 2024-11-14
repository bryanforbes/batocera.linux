from __future__ import annotations

from typing import TYPE_CHECKING, Final, Literal, overload

if TYPE_CHECKING:
    import enum

    class _MISSING_TYPE(enum.Enum):
        MISSING = enum.auto()

        @overload
        def __eq__(self, other: MissingType) -> Literal[True]:  # pyright: ignore[reportOverlappingOverload]
            ...

        @overload
        def __eq__(self, other: object) -> Literal[False]:
            ...

        def __eq__(self, other: object) -> bool:
            ...

        def __ne__(self, other: object) -> Literal[False]:
            ...

        def __lt__(self, other: object) -> Literal[False]:
            ...

        def __gt__(self, other: object) -> Literal[False]:
            ...

        def __bool__(self) -> Literal[False]:
            ...

        def __hash__(self) -> int:
            ...

        def __repr__(self) -> str:
            ...

    MISSING: Final = _MISSING_TYPE.MISSING
    type MissingType = Literal[_MISSING_TYPE.MISSING]
else:
    class _MissingSentinel:
        __slots__ = ()

        def __eq__(self, other: object) -> bool:
            return other is self

        def __ne__(self, other: object) -> Literal[False]:
            return False

        def __lt__(self, other: object) -> Literal[False]:
            return False

        def __gt__(self, other: object) -> Literal[False]:
            return False

        def __bool__(self) -> Literal[False]:
            return False

        def __hash__(self) -> int:
            return 0

        def __repr__(self) -> str:
            return '...'

    type MissingType = _MissingSentinel
    MISSING: Final[MissingType] = _MissingSentinel()
