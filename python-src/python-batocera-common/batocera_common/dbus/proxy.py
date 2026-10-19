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

import asyncio
import inspect
import itertools
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Protocol, overload

from dbus_fast import Message, MessageType, Variant
from dbus_fast._private.util import replace_fds_with_idx, replace_idx_with_fds
from dbus_fast.proxy_object import BaseProxyInterface

from batocera_common.dataclasses import cached_dataclass, cached_property

if TYPE_CHECKING:
    from dbus_fast.aio import MessageBus


@dataclass(slots=True, frozen=True)
class DBusObjectProxy:
    _dbus_bus: MessageBus
    _dbus_bus_name: str
    _dbus_path: str

    def get_proxy[P: DBusProxy](self, proxy_cls: type[P], /) -> P:
        return proxy_cls(self._dbus_bus, self._dbus_bus_name, self._dbus_path)


class SyncCallback[*Ts](Protocol):
    def __call__(self, *args: *Ts) -> object: ...


class AsyncCallback[*Ts](Protocol):
    async def __call__(self, *args: *Ts) -> object: ...


type DBusCallback[*Ts] = SyncCallback[*Ts] | AsyncCallback[*Ts]
type DBusPropertyCallback[T] = DBusCallback[T | None]
type Unwatch = Callable[[], None]


@cached_dataclass(frozen=True)
class DBusProxy:
    __dbus_interface_name__: ClassVar[str]

    __dbus_method_signatures__: ClassVar[dict[str, tuple[str, str | None]]] = {}
    __dbus_property_signatures__: ClassVar[dict[str, str]] = {}
    __dbus_signal_signatures__: ClassVar[dict[str, str]] = {}

    _dbus_bus: MessageBus = field(repr=False)
    _dbus_bus_name: str
    _dbus_path: str

    __properties_signals_unwatch: Unwatch | None = field(init=False, repr=False, default=None)
    __property_callbacks: dict[str, list[DBusPropertyCallback[Any]]] = field(
        init=False, repr=False, default_factory=lambda: defaultdict(list)
    )
    __all_properties_callbacks: list[DBusCallback[Any, list[str]]] = field(
        init=False, repr=False, default_factory=list[DBusCallback[Any, list[str]]]
    )
    __signal_callbacks: dict[str, list[DBusCallback[*tuple[Any, ...]]]] = field(
        init=False, repr=False, default_factory=lambda: defaultdict(list)
    )
    __tasks: set[asyncio.Task[object]] = field(init=False, repr=False, default_factory=set[asyncio.Task[object]])

    @cached_property
    def __dbus_match_rule(self) -> str:
        return f"type='signal',sender={self._dbus_bus_name},interface={self.__dbus_interface_name__},path={self._dbus_path}"

    @cached_property
    def __properties_proxy(self) -> FreedesktopDBusProperties:
        return FreedesktopDBusProperties(self._dbus_bus, self._dbus_bus_name, self._dbus_path)

    async def _call(self, method_name: str, *args: Any) -> Any:
        signature, return_signature = self.__dbus_method_signatures__.get(method_name, (None, None))

        if signature is None:
            raise RuntimeError(f'Method {method_name!r} is not defined in {self.__class__.__name__!r}')

        input_body, unix_fds = replace_fds_with_idx(signature, list(args))

        reply = await self._dbus_bus.call(
            Message(
                destination=self._dbus_bus_name,
                path=self._dbus_path,
                interface=self.__dbus_interface_name__,
                member=method_name,
                signature=signature,
                body=input_body,
                unix_fds=unix_fds,
            )
        )

        BaseProxyInterface._check_method_return(reply, return_signature or '')

        reply_body = replace_idx_with_fds(reply.signature_tree, reply.body, reply.unix_fds)

        if not reply_body:
            return None

        if len(reply_body) == 1:
            return reply_body[0]

        return tuple(reply_body)

    async def _get(self, name: str, /) -> Any:
        if (signature := self.__dbus_property_signatures__.get(name)) is None:
            raise RuntimeError(f'Property {name!r} is not defined in {self.__class__.__name__!r}')

        variant = await self.__properties_proxy.call('Get', self.__dbus_interface_name__, name)

        if variant.signature != signature:
            raise RuntimeError(f'Property {name!r}: expected signature {signature!r}, received {variant.signature!r}')

        return variant.value

    async def _set(self, name: str, value: Any, /) -> None:
        if (signature := self.__dbus_property_signatures__.get(name)) is None:
            raise RuntimeError(f'Property {name!r} is not defined in {self.__class__.__name__!r}')

        variant = Variant(signature, value)

        await self.__properties_proxy.call('Set', self.__dbus_interface_name__, name, variant)

    async def _get_all(self) -> Any:
        properties = await self.__properties_proxy.call('GetAll', self.__dbus_interface_name__)

        return {key: value.value for key, value in properties.items()}

    def _watch_all(self, callback: DBusCallback[Any, list[str]], /) -> Unwatch:
        if callback in self.__all_properties_callbacks:
            return lambda: None

        def on_properties_changed(
            interface: str, changed_properties: dict[str, Variant], invalidated_properties: list[str], /
        ) -> None:
            if interface != self.__dbus_interface_name__:
                return

            self.__run_callback(
                callback,
                {key: value.value for key, value in changed_properties.items()},
                invalidated_properties,
            )

        unwatch = self.__properties_proxy.on('PropertiesChanged', on_properties_changed)
        self.__all_properties_callbacks.append(callback)

        removed = False

        def remove_callback() -> None:
            nonlocal removed

            if removed:
                return

            removed = True
            unwatch()
            self.__all_properties_callbacks.remove(callback)

        return remove_callback

    def __on_properties_changed(
        self, interface: str, changed_properties: dict[str, Variant], invalidated_properties: list[str]
    ) -> None:
        if interface != self.__dbus_interface_name__:
            return

        for name, value in itertools.chain(
            changed_properties.items(), ((name, None) for name in invalidated_properties)
        ):
            for callback in tuple(self.__property_callbacks[name]):
                self.__run_callback(callback, value.value if value is not None else None)

    def _add_property_callback(self, property_name: str, callback: DBusPropertyCallback[Any], /) -> Unwatch:
        if callback in self.__property_callbacks[property_name]:
            return lambda: None

        self.__property_callbacks[property_name].append(callback)

        if self.__properties_signals_unwatch is None:
            object.__setattr__(
                self,
                '_DBusProxy__properties_signals_unwatch',
                self.__properties_proxy.on('PropertiesChanged', self.__on_properties_changed),
            )

        removed = False

        def remove_callback() -> None:
            nonlocal removed

            if removed:
                return

            removed = True
            self.__remove_property_callback(property_name, callback)

        return remove_callback

    def __remove_property_callback(self, property_name: str, callback: DBusPropertyCallback[Any], /) -> None:
        if callback not in self.__property_callbacks[property_name]:
            return

        if self.__properties_signals_unwatch is None:
            return

        self.__property_callbacks[property_name].remove(callback)

        if not any(self.__property_callbacks.values()):
            self.__properties_signals_unwatch()
            object.__setattr__(self, '_DBusProxy__properties_signals_unwatch', None)

    def __message_handler(self, message: Message, /) -> None:
        if (
            message.message_type != MessageType.SIGNAL
            or message.interface != self.__dbus_interface_name__
            or message.path != self._dbus_path
            or message.member not in self.__signal_callbacks
            or not (callbacks := self.__signal_callbacks[message.member])
        ):
            return

        if (
            message.sender != self._dbus_bus_name
            and self._dbus_bus._name_owners.get(self._dbus_bus_name, '') != message.sender
        ):
            return

        if message.signature != self.__dbus_signal_signatures__.get(message.member):
            return

        body = replace_idx_with_fds(message.signature, message.body, message.unix_fds)

        for callback in tuple(callbacks):
            self.__run_callback(callback, *body)

    def _add_signal_callback(self, signal_name: str, callback: DBusCallback[*tuple[Any, ...]], /) -> Unwatch:
        if callback in self.__signal_callbacks[signal_name]:
            return lambda: None

        python_signature = inspect.signature(callback)

        if any(
            parameter
            for parameter in python_signature.parameters.values()
            if parameter.kind == parameter.KEYWORD_ONLY and parameter.default == parameter.empty
        ):
            raise TypeError('Signal callback cannot have required keyword-only parameters')

        had_callbacks = any(self.__signal_callbacks.values())

        self.__signal_callbacks[signal_name].append(callback)

        if not had_callbacks:
            self._dbus_bus._add_match_rule(self.__dbus_match_rule)
            self._dbus_bus.add_message_handler(self.__message_handler)

        removed = False

        def remove_callback() -> None:
            nonlocal removed

            if removed:
                return

            removed = True
            self.__remove_signal_callback(signal_name, callback)

        return remove_callback

    def __remove_signal_callback(self, name: str, callback: DBusCallback[*tuple[Any, ...]], /) -> None:
        if callback not in self.__signal_callbacks[name]:
            return

        self.__signal_callbacks[name].remove(callback)

        if any(self.__signal_callbacks.values()):
            return

        self._dbus_bus._remove_match_rule(self.__dbus_match_rule)
        self._dbus_bus.remove_message_handler(self.__message_handler)

    def __run_callback[*Ts](self, callback: DBusCallback[*Ts], *args: *Ts) -> None:
        result = callback(*args)

        if inspect.iscoroutine(result):
            # Save a strong reference to the task so it doesn't get garbage
            # collected before it finishes.
            task = asyncio.create_task(result)
            self.__tasks.add(task)
            task.add_done_callback(self.__tasks.remove)


@cached_dataclass(frozen=True)
class FreedesktopDBusProperties(DBusProxy):
    __dbus_interface_name__: ClassVar[str] = 'org.freedesktop.DBus.Properties'

    __dbus_method_signatures__: ClassVar[dict[str, tuple[str, str | None]]] = {
        'Get': ('ss', 'v'),
        'GetAll': ('s', 'a{sv}'),
        'Set': ('ssv', ''),
    }
    __dbus_signal_signatures__: ClassVar[dict[str, str]] = {
        'PropertiesChanged': 'sa{sv}as',
    }

    @overload
    async def call(self, name: Literal['Get'], interface_name: str, property_name: str, /) -> Variant: ...
    @overload
    async def call(self, name: Literal['GetAll'], interface_name: str, /) -> dict[str, Variant]: ...
    @overload
    async def call(self, name: Literal['Set'], interface_name: str, property_name: str, value: Variant, /) -> None: ...
    async def call(self, name: str, *args: Any) -> Any:
        return await self._call(name, *args)

    def on(
        self, name: Literal['PropertiesChanged'], callback: DBusCallback[str, dict[str, Variant], list[str]], /
    ) -> Unwatch:
        return self._add_signal_callback(name, callback)
