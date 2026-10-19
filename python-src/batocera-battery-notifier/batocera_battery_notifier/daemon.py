from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Literal

from batocera_common.asyncio import run
from batocera_common.dbus import Bus
from batocera_common.dbus.proxies.upower import UPower
from batocera_common.dbus.proxies.upower_device import UPowerDevice, _UPowerDeviceChangedProperties


class DeviceState(IntEnum):
    Unknown = 0
    Charging = 1
    Discharging = 2
    Empty = 3
    FullyCharged = 4
    PendingCharge = 5
    PendingDischarge = 6


def _flash_screen(delay: int) -> None: ...


@dataclass(slots=True)
class Daemon:
    upower: UPower = field(init=False, repr=False)
    display_device: UPowerDevice = field(init=False, repr=False)

    policy: Literal['ac', 'battery'] | None = field(init=False, repr=False, default=None)
    battery_percentage: float = field(init=False, repr=False, default=0.0)
    battery_state: DeviceState = field(init=False, repr=False, default=DeviceState.Unknown)

    changed_event: asyncio.Event = field(init=False, repr=False, default_factory=asyncio.Event)

    async def __on_battery_changed(self, on_battery: bool | None, /) -> None:
        if on_battery is None:
            on_battery = await self.upower.get('OnBattery')

        policy = 'battery' if on_battery else 'ac'

        if self.policy != policy:
            await run('/usr/bin/batocera-power-mode', policy)
            self.policy = policy

            self.changed_event.set()

    async def __on_display_device_changed(
        self, properties: _UPowerDeviceChangedProperties, invalidated: list[str], /
    ) -> None:
        changed = False

        if (state := properties.get('State')) is not None:
            self.battery_state = DeviceState(state)
            changed = True
        elif 'State' in invalidated:
            self.battery_state = DeviceState(await self.display_device.get('State'))
            changed = True

        if (percentage := properties.get('Percentage')) is not None:
            self.battery_percentage = percentage
            changed = True
        elif 'Percentage' in invalidated:
            self.battery_percentage = await self.display_device.get('Percentage')
            changed = True

        if changed:
            self.changed_event.set()

    async def __loop(self) -> None:
        while True:
            last_battery_percentage = self.battery_percentage

            await self.changed_event.wait()
            self.changed_event.clear()

            if self.policy != 'battery' or self.battery_state != DeviceState.Discharging:
                continue

            if self.battery_percentage < last_battery_percentage and self.battery_percentage <= 10:
                delay = 4

                if self.battery_percentage <= 5:
                    delay = 10

                _flash_screen(delay)

    async def run(self) -> None:
        async with Bus() as bus:
            self.upower = bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower').get_proxy(UPower)
            self.display_device = bus.get_object(
                'org.freedesktop.UPower', await self.upower.call('GetDisplayDevice')
            ).get_proxy(UPowerDevice)

            unwatch_on_battery = self.upower.watch('OnBattery', self.__on_battery_changed)
            await self.__on_battery_changed(None)

            unwatch_display_device = self.display_device.watch_all(self.__on_display_device_changed)
            all_properties = await self.display_device.get_all()
            self.battery_percentage = all_properties['Percentage']
            self.battery_state = DeviceState(all_properties['State'])

            try:
                await self.__loop()
            finally:
                unwatch_display_device()
                unwatch_on_battery()
