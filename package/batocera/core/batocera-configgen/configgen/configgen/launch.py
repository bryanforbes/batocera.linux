from __future__ import annotations

from collections import ChainMap
from contextlib import asynccontextmanager
from dataclasses import InitVar, asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, cast

from batocera_launch import (
    Command,
    Emulator,
    HotkeysContext,
    SystemConfig,
    cached_dataclass,
    cached_property,
)

from .config import Config, SystemConfig as _SystemConfig
from .Emulator import Emulator as _System
from .generators.importer import get_generator

if TYPE_CHECKING:
    from argparse import Namespace
    from collections.abc import AsyncGenerator

    from batocera_launch.devices.device import DeviceInfo
    from configgen.generators.Generator import Generator
    from configgen.types import DeviceInfo as _DeviceInfo


def _convert_device_info(device_info: DeviceInfo, /) -> _DeviceInfo:
    result: _DeviceInfo = {
        'eventId': device_info.event_id,
        'sysfs_path': device_info.sysfs_path,
        'isJoystick': device_info.is_joystick,
        'isWheel': device_info.is_wheel,
        'isMouse': device_info.is_mouse,
        'associatedDevices': device_info.associated_devices,
        'joystick_index': device_info.joystick_index,
        'mouse_index': device_info.mouse_index,
    }

    if device_info.wheel_rotation is not None:
        result['wheel_rotation'] = device_info.wheel_rotation

    return result


@dataclass
class GeneratorSystemConfig(_SystemConfig):
    @classmethod
    def from_launch(cls, config: SystemConfig, /) -> Self:
        overlay: dict[str, Any] = {
            'emulator': config.emulator,
            'emulator-forced': config.emulator_forced,
            'core': config.core,
            'core-forced': config.core_forced,
            'uimode': config.ui_mode,
            'showFPS': config.show_fps,
            'use_guns': config.use_guns,
            'use_wheels': config.use_wheels,
        }

        if config.netplay_mode is not None:
            overlay['netplay.mode'] = config.netplay_mode

        if config.netplay_password is not None:
            overlay['netplay.password'] = config.netplay_password

        if config.netplay_server_ip is not None:
            overlay['netplay.server.ip'] = config.netplay_server_ip

        if config.netplay_server_port is not None:
            overlay['netplay.server.port'] = config.netplay_server_port

        if config.netplay_server_session is not None:
            overlay['netplay.server.session'] = config.netplay_server_session

        if config.state_slot is not None:
            overlay['state_slot'] = config.state_slot

        if config.autosave is not None:
            overlay['autosave'] = config.autosave

        if config.state_filename is not None:
            overlay['state_filename'] = config.state_filename

        return cls(cast('dict[str, Any]', ChainMap(overlay, config.data)))


@dataclass(slots=True)
class GeneratorSystem(_System):
    launch_config: InitVar[SystemConfig]

    def __post_init__(self, args: Namespace, rom: Path, launch_config: SystemConfig, /) -> None:
        self.name = args.system
        self.game_info_xml = str(args.gameinfoxml)
        self.config = GeneratorSystemConfig.from_launch(launch_config)
        self.renderconfig = Config(dict(launch_config.render_config.data))


@cached_dataclass
class GeneratorEmulator(Emulator):
    generator: Generator
    configgen_system: GeneratorSystem

    @cached_property
    def hotkeygen_context(self) -> HotkeysContext:
        return self.generator.getHotkeysContext()

    @property
    def execution_path(self) -> Path | None:
        return self.generator.executionDirectory(self.configgen_system.config, self.rom)

    @property
    def target_video_mode(self) -> str:
        return self.generator.getResolutionMode(self.configgen_system.config) or 'default'

    @property
    def needs_mouse(self) -> bool:
        return self.generator.getMouseMode(self.configgen_system.config, self.rom)

    @property
    def handles_bezels(self) -> bool:
        return self.generator.supportsInternalBezels()

    @property
    def handles_hud(self) -> bool:
        return self.generator.hasInternalMangoHUDCall()

    @property
    def needs_overlayfs(self) -> bool:
        return self.generator.writesToRom(self.configgen_system.config)

    @cached_property
    def in_game_ratio(self) -> float:
        return self.generator.getInGameRatio(
            self.configgen_system.config,
            {
                'width': self.resolution.width,
                'height': self.resolution.height,
            },
            self.rom,
        )

    @cached_property
    def guns_borders_size(self) -> str | None:
        return self.configgen_system.guns_borders_size_name(self.guns)  # pyright: ignore[reportArgumentType]

    async def configure(self) -> Command:
        command = self.generator.generate(
            self.configgen_system,
            Path(self.rom),
            self.controllers,  # pyright: ignore
            self.metadata,
            self.guns,  # pyright: ignore
            {key: _convert_device_info(wheel) for key, wheel in self.wheels.items()},
            asdict(self.resolution),  # pyright: ignore
        )

        return Command(
            command.array,
            command.env,
        )

    @classmethod
    @asynccontextmanager
    async def prepare_emulator(cls, args: Namespace, max_players: int, /) -> AsyncGenerator[Self]:
        system_config = SystemConfig.load(args)

        generator = get_generator(system_config.emulator, system_config.core)
        emulator = cls(
            args.system,
            args.systemname,
            system_config,
            args.gameinfoxml,
            generator,
            GeneratorSystem(args, args.rom, system_config),
        )

        async with emulator._prepare_devices_and_data(args, max_players) as emulator:
            yield emulator
