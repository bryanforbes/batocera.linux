# This file is part of The Batocera Linux Distribution (https://batocera.org).
# Copyright (c) 2026 The Batocera Team.
#
# The Batocera Linux Distribution is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# The Batocera Linux Distribution is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with The Batocera Linux Distribution. If not, see
# <https://www.gnu.org/licenses/>.
#
# YOU MUST RETAIN THE LICENSE AND COPYRIGHT NOTICES ABOVE IN ANY
# REDISTRIBUTED VERSION OF THIS FILE.

from __future__ import annotations

from typing import Annotated, Final

from dbus_fast import Variant
from dbus_fast.annotations import DBusSignature

from hotkeygen._types import DeviceTuple, KeysMappingDict

DBUS_BUS_NAME: Final = 'org.batocera.Hotkeygen'
DBUS_PATH: Final = '/'

HOTKEYGEN_INTERFACE: Final = 'org.batocera.Hotkeygen'

type DBusContextType = tuple[str, dict[str, Variant]]
type DBusDeviceMappingsType = list[tuple[DeviceTuple, tuple[KeysMappingDict, KeysMappingDict]]]

DBusContext = Annotated[DBusContextType, DBusSignature('(sa{sv})')]
DBusDetails = Annotated[
    tuple[DBusContextType, DBusDeviceMappingsType], DBusSignature('((sa{sv})a((ssss)(a{ts}a{ts})))')
]

DBusDeviceMappingConfig = Annotated[dict[str, dict[str, str]], DBusSignature('a{sa{ss}}')]
DBusSystemDefaultMappingConfig = Annotated[tuple[dict[str, str], dict[str, str]], DBusSignature('(a{ss}a{ss})')]
