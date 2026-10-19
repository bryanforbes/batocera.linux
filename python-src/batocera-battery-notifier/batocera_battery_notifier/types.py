from __future__ import annotations

from typing import Annotated, Literal

from dbus_fast.annotations import DBusSignature

type CriticalAction = Literal['HybridSleep', 'Hibernate', 'PowerOff']

DBusPathList = Annotated[list[str], DBusSignature('ao')]
DBusCriticalAction = Annotated[CriticalAction, DBusSignature('s')]
DBusHistoryData = Annotated[list[tuple[int, float, int]], DBusSignature('a(udu)')]
DBusStatistics = Annotated[list[tuple[float, float]], DBusSignature('a(dd)')]
DBusBrightnessWithSource = Annotated[tuple[int, str], DBusSignature('(is)')]
