from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


@dataclass(slots=True)
class HotkeyActivation:
    _finish: Callable[[], Awaitable[None]]
    _cancel: Callable[[], Awaitable[None]]
    _completed: bool = field(init=False, default=False)

    async def finish(self) -> None:
        if self._completed:
            return

        self._completed = True
        await self._finish()

    async def cancel(self) -> None:
        if self._completed:
            return

        self._completed = True
        await self._cancel()
