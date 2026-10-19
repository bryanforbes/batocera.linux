# ruff: ignore[missing-required-import]

# NOTE: in order for dbus_fast to properly introspect the annotations
# this file CANNOT use `from __future__ import annotations`

import asyncio
import json
from copy import deepcopy
from typing import TYPE_CHECKING, Annotated, Final

from dbus_fast import PropertyAccess, Variant
from dbus_fast.annotations import DBusBool, DBusSignature, DBusStr, DBusUInt64
from dbus_fast.errors import DBusError

from batocera_common.dbus import Service, dbus_method, dbus_property
from batocera_common.fs import atomic_write
from batocera_common.paths import existing_files_in_directories, glob_in_directories

from ..paths import CONFIG_DEFAULTDIR, CONFIG_SYSTEMDIR, CONFIG_USERDIR, CONTEXT_FILE, SYSTEM_DEFAULT_MAPPING
from ..utils import get_device_config_filename, get_hotkeys_context
from .common import (
    HOTKEYGEN_INTERFACE,
    DBusContext,
    DBusContextType,
    DBusDetails,
    DBusDeviceMappingConfig,
    DBusDeviceMappingsType,
    DBusSystemDefaultMappingConfig,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
    from pathlib import Path

    import evdev

    from .._types import DevicesMappingsDict, HotkeysContext, HotkeysContextMapping, PersistedHotkeysContext
    from ..activation import HotkeyActivation


DBusKeysDict = Annotated[dict[str, Variant], DBusSignature('a{sv}')]


_DEFAULT_CONTEXT_FILE: Final = CONFIG_DEFAULTDIR / 'default_context.conf'


# default context is for ES
def _load_default_context() -> HotkeysContextMapping:
    context: HotkeysContextMapping | None = None

    if _DEFAULT_CONTEXT_FILE.exists():
        try:
            context = json.loads(_DEFAULT_CONTEXT_FILE.read_text())
        except Exception as e:
            print(f'failed to load default context file : {e}')

    if context is None:
        context = {'name': '', 'keys': {}}

    return context


def _load_initial_context(debug: bool) -> HotkeysContext:
    context: HotkeysContextMapping | None = None
    include_common = True

    if CONTEXT_FILE.exists():
        try:
            persisted: PersistedHotkeysContext = json.loads(CONTEXT_FILE.read_text())

            context = persisted.get('context')
            include_common = persisted.get('include_common', True)
        except Exception as e:
            print(f'failed to load persisted context file : {e}')

    if context is None:
        context = _load_default_context()
        include_common = True

    return get_hotkeys_context(context, include_common, debug=debug)


class HotkeygenService(Service):
    __dbus_interface_name__ = HOTKEYGEN_INTERFACE

    def __init__(
        self,
        debug: bool,
        *,
        run_tracked_action: Callable[[Callable[[], Awaitable[object]]], Awaitable[None]],
        iterate_connected_devices: Callable[[], Iterator[evdev.InputDevice[str]]],
        reload_device_mappings: Callable[[], object],
        get_device_mappings: Callable[[], DevicesMappingsDict],
        reset_mouse_position: Callable[[], Awaitable[object]],
        begin_hotkey: Callable[[str], Awaitable[HotkeyActivation | None]],
    ) -> None:
        self.debug = debug

        self.__run_tracked_action = run_tracked_action
        self.__iterate_connected_devices = iterate_connected_devices
        self.__reload_device_mappings = reload_device_mappings
        self.__get_device_mappings = get_device_mappings
        self.__reset_mouse_position = reset_mouse_position
        self.__begin_hotkey = begin_hotkey

        self.__context = _load_initial_context(debug)
        self.__context_event = asyncio.Event()

        super().__init__()

    @property
    def context(self) -> HotkeysContext:
        return self.__context

    @context.setter
    def context(self, value: HotkeysContext) -> None:
        changed = getattr(self, '_HotkeygenService__context', None) != value

        self.__context = value

        if changed:
            self.__context_event.set()

    async def context_changed(self) -> AsyncIterator[HotkeysContext]:
        while True:
            await self.__context_event.wait()

            try:
                yield self.context
            finally:
                self.__context_event.clear()
                self.emit_properties_changed({'Context': self.dbus_context})

    @dbus_property(name='Context', access=PropertyAccess.READ)
    def dbus_context(self) -> DBusContext:
        context = deepcopy(self.context)

        dbus_context: DBusContextType = (
            context['name'],
            {
                action: Variant('s' if isinstance(keys, str) else 't' if isinstance(keys, int) else 'at', keys)
                for action, keys in context['keys'].items()
            },
        )

        return dbus_context

    def __set_context(self, context: HotkeysContextMapping | None, /, include_common: bool = True) -> None:
        previous_context = self.context
        persist_context = context is not None

        if context is None:
            try:
                CONTEXT_FILE.unlink(missing_ok=True)
            except Exception as e:
                print(f'failed to remove persisted context: {e}')

            context = _load_default_context()

        self.context = get_hotkeys_context(context, include_common, debug=self.debug)

        if persist_context:
            try:
                with atomic_write(CONTEXT_FILE) as context_file:
                    context_file.write_text(
                        json.dumps(
                            {
                                'context': context,
                                'include_common': include_common,
                            },
                            indent=4,
                        )
                    )
            except Exception as e:
                print(f'failed to persist context: {e}')

        self.__reload_device_mappings()

        if previous_context != self.context:
            self.__context_event.set()

    async def __send_hotkey(self, hotkey: str, delay: int | None, /) -> None:
        if self.debug:
            if delay:
                print(f'Sending {hotkey} with delay {delay}')
            else:
                print(f'Sending {hotkey}')

        if (activation := await self.__begin_hotkey(hotkey)) is None:
            return

        try:
            # time required for emulators (like mame) based on states and not on events
            # (if you go too fast, the event is not seen, so we default to 0.3)
            await asyncio.sleep(delay or 0.3)
        except BaseException:
            await activation.cancel()
            raise
        finally:
            await activation.finish()

    @dbus_method(name='SetContext')
    def set_context(self, name: DBusStr, keys: DBusKeysDict, include_common: DBusBool, /) -> None:
        python_keys: dict[str, str | list[str]] = {}

        for key, variant in keys.items():
            if variant.signature not in ('s', 'as'):
                raise DBusError(
                    'org.batocera.Hotkeygen.InvalidKeys',
                    f'Invalid variant signature for key {key}: {variant.signature}',
                )

            python_keys[key] = variant.value

        self.__set_context({'name': name, 'keys': python_keys}, include_common=include_common)

    @dbus_method(name='SetDefaultContext')
    def set_default_context(self) -> None:
        self.__set_context(None, include_common=True)

    @dbus_method(name='GetDetails')
    def get_details(self) -> DBusDetails:
        dbus_mappings: DBusDeviceMappingsType = [
            (device, (mapping, associations))
            for device, (mapping, associations) in self.__get_device_mappings().items()
        ]

        return (self.dbus_context, dbus_mappings)

    @dbus_method(name='Reload')
    def reload(self) -> None:
        if not self.context['name']:
            self.set_default_context()
        else:
            self.__reload_device_mappings()

    @dbus_method(name='ResetMousePosition')
    async def reset_mouse_position(self) -> None:
        await self.__run_tracked_action(self.__reset_mouse_position)

    @dbus_method(name='SendHotkey')
    async def send_hotkey(self, hotkey: DBusStr, delay: DBusUInt64, /) -> None:
        await self.__run_tracked_action(lambda: self.__send_hotkey(hotkey, delay))

    @dbus_method(name='GetSystemDefaultMappingConfig')
    def get_system_default_mapping_config(self) -> DBusSystemDefaultMappingConfig:
        by_keys: dict[str, str] = json.loads(SYSTEM_DEFAULT_MAPPING.read_text())
        by_names: dict[str, str] = {name: key for key, name in by_keys.items()}

        return by_keys, by_names

    def __get_connected_mapping_files(self) -> Iterator[Path]:
        connected_mapping_filenames = {
            get_device_config_filename(device) for device in self.__iterate_connected_devices()
        }

        seen_user_mappings = set[str]()

        for file in glob_in_directories('*.mapping', (CONFIG_USERDIR, CONFIG_SYSTEMDIR)):
            if not file.is_file():
                continue

            if file.is_relative_to(CONFIG_SYSTEMDIR) and (
                file.name in seen_user_mappings or file.name not in connected_mapping_filenames
            ):
                continue
            else:
                seen_user_mappings.add(file.name)

            yield file

    @dbus_method(name='GetDeviceMappingConfig')
    def get_device_mapping_config(self) -> DBusDeviceMappingConfig:
        device_mappings: dict[str, dict[str, str]] = {}

        for mapping_file in self.__get_connected_mapping_files():
            try:
                values = json.loads(mapping_file.read_text())
            except Exception as e:
                print(f'error while reading mapping file "{mapping_file}": {e}')
                continue

            device_mappings[mapping_file.name] = values

        return device_mappings

    def __write_device_mapping_config(self, filename: str, key: str, action: str | None, /) -> None:
        if not filename.endswith('.mapping'):
            raise ValueError(f'filename must end with .mapping, got {filename!r}')

        user_file = CONFIG_USERDIR / filename

        values: dict[str, str] = {}

        # read the user file. if not, read the system file (but always write in the user file)
        for path in existing_files_in_directories(filename, (CONFIG_USERDIR, CONFIG_SYSTEMDIR)):
            values = json.loads(path.read_text())
            break

        if action is None:
            values.pop(key, None)
        else:
            values[key] = '' if action == 'none' else action

        user_file.parent.mkdir(parents=True, exist_ok=True)

        with atomic_write(user_file) as user_file:
            user_file.write_text(json.dumps(values, indent=4))

        self.__reload_device_mappings()

    @dbus_method(name='SetDeviceMappingConfig')
    def set_device_mapping_config(self, filename: DBusStr, key: DBusStr, action: DBusStr, /) -> None:
        self.__write_device_mapping_config(filename, key, action)

    @dbus_method(name='RemoveDeviceMappingConfig')
    def remove_device_mapping_config(self, filename: DBusStr, key: DBusStr, /) -> None:
        self.__write_device_mapping_config(filename, key, None)
