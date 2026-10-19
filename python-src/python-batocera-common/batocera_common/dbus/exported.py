from __future__ import annotations

from dataclasses import dataclass

from batocera_common.dbus import Service


@dataclass(slots=True, frozen=True)
class DBusExported[S: Service]:
    _dbus_path: str
    _dbus_service: S

    @property
    def path(self) -> str:
        return self._dbus_path

    @property
    def service(self) -> S:
        return self._dbus_service
