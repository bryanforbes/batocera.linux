from __future__ import annotations

import logging
import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import evdev

from .batoceraPaths import BATOCERA_SHARE_DIR, CONFIGS, SAVES, mkdir_if_not_exists

if TYPE_CHECKING:
    from .Emulator import Emulator

_input_re = re.compile(r"^/dev/input/event([0-9]*)$")
_logger = logging.getLogger(__name__)

_mouse_code_to_button: Final = {
    evdev.ecodes.BTN_LEFT: 'left',
    evdev.ecodes.BTN_RIGHT: 'right',
    evdev.ecodes.BTN_MIDDLE: 'middle',
    evdev.ecodes.BTN_1: '1',
    evdev.ecodes.BTN_2: '2',
    evdev.ecodes.BTN_3: '3',
    evdev.ecodes.BTN_4: '4',
    evdev.ecodes.BTN_5: '5',
    evdev.ecodes.BTN_6: '6',
    evdev.ecodes.BTN_7: '7',
    evdev.ecodes.BTN_8: '8',
}

_mouse_button_to_code: Final = {button: code for code, button in _mouse_code_to_button.items()}

_PRECALIBRATION_DIR: Final = BATOCERA_SHARE_DIR / "guns-precalibrations"

def _get_mouse_buttons(device: evdev.InputDevice) -> list[str]:
    caps_keys = device.capabilities()[evdev.ecodes.EV_KEY]
    mouse_caps = set(caps_keys) & set(_mouse_code_to_button.keys())

    return [button for cap, button in _mouse_code_to_button.values() if cap in mouse_caps]


def _copy_file(src: Path, dst: Path) -> None:
    if src.exists() and not dst.exists():
        mkdir_if_not_exists(dst.parent)
        shutil.copyfile(src, dst)

def _copy_dir(src: Path, dst: Path) -> None:
    if src.exists() and not dst.exists():
        mkdir_if_not_exists(dst.parent)
        shutil.copytree(src, dst)

def _copy_fils_in_dir(srcdir: Path, dstdir: Path, starts_with: str, ends_with: str) -> None:
    for src in srcdir.iterdir():
        if src.name.startswith(starts_with): # and src.endswith(ends_with):
            _copy_file(src, dstdir / src.name)


@dataclass(slots=True, kw_only=True)
class Gun:
    node: str
    mouse_index: int
    need_cross: bool
    need_borders: bool
    name: str
    buttons: list[str]

    @classmethod
    def get_all(cls) -> GunDict:
        import pyudev

        guns: GunDict = {}
        context = pyudev.Context()

        mouses = {
            int(match.group(1)): mouse
            for mouse in context.list_devices(subsystem='input')
            if mouse.device_node is not None and
            (match := _input_re.match(mouse.device_node)) is not None and
            mouse.properties.get("ID_INPUT_MOUSE") == '1'
        }

        gun_index = 0
        for mouse_index, (_, mouse) in enumerate(sorted(mouses.items(), key=lambda item: item[0])):
            _logger.info("found mouse %s at %s with mouse_index=%s", mouse_index, mouse.device_node, mouse_index)
            if "ID_INPUT_GUN" not in mouse.properties or mouse.properties["ID_INPUT_GUN"] != "1":
                continue

            device = evdev.InputDevice(cast(str, mouse.device_node))

            guns[gun_index] = cls(
                node=cast(str, mouse.device_node),
                mouse_index=mouse_index,
                # retroarch uses mouse indexes into configuration files using ID_INPUT_MOUSE (TOUCHPAD are listed after mouses)
                need_cross=mouse.properties.get("ID_INPUT_GUN_NEED_CROSS") == '1',
                need_borders=mouse.properties.get("ID_INPUT_GUN_NEED_BORDERS") == '1',
                name=device.name,
                buttons=_get_mouse_buttons(device)
            )

            gun_index += 1

        if not guns:
            _logger.info("no guns found")

        return guns

    @classmethod
    def get_and_precalibrate_all(cls, system_name: str, system: Emulator, rom: str | Path, /) -> GunDict:
        if not system.get_option_bool('use_guns'):
            _logger.info("guns disabled.")
            return {}

        dir = _PRECALIBRATION_DIR / system_name

        if dir.exists():
            emulator = system.emulator
            core = system.core
            rom = Path(rom)

            if system_name == "atomiswave":
                for suffix in ["nvmem", "nvmem2"]:
                    src = dir / "reicast" / f"{rom.name}.{suffix}"
                    dst = SAVES / "atomiswave" / "reicast" / f"{rom.name}.{suffix}"
                    _copy_file(src, dst)

            elif system_name == "mame":
                target_dir: str | None = None
                if emulator == "mame":
                    target_dir = "mame"
                elif emulator == "libretro":
                    if core == "mame078plus":
                        target_dir = "mame/mame2003-plus"
                    elif core == "mame":
                        target_dir = "mame/mame"

                if target_dir is not None:
                    src = dir / "nvram" / rom.stem
                    dst = SAVES / target_dir / "nvram" / rom.stem
                    _copy_dir(src, dst)
                    srcdir = dir / "diff"
                    dstdir = SAVES / target_dir / "diff"
                    _copy_fils_in_dir(srcdir, dstdir, rom.stem + "_", ".dif")

            elif system_name == "model2":
                src = dir / "NVDATA" / f"{rom.name}.DAT"
                dst = SAVES / "model2" / "NVDATA" / f"{rom.name}.DAT"
                _copy_file(src, dst)

            elif system_name == "naomi":
                for suffix in ["nvmem", "eeprom"]:
                    src = dir / "reicast" / f"{rom.name}.{suffix}"
                    dst = SAVES / "naomi" / "reicast" / f"{rom.name}.{suffix}"
                    _copy_file(src, dst)

            elif system_name == "supermodel":
                src = dir / "NVDATA" / f"{rom.stem}.nv"
                dst = SAVES / "supermodel" / "NVDATA" / f"{rom.stem}.nv"
                _copy_file(src, dst)

            elif system_name == "namco2x6" and emulator == "play":
                src = dir / "play" / rom.stem
                dst = CONFIGS / "play" / "Play Data Files" / "arcadesaves" / f"{rom.stem}.backupram"
                _copy_file(src, dst)

        return cls.get_all()


def gun_button_to_code(button: str) -> int | None:
    return _mouse_button_to_code.get(button)


def guns_need_crosses(guns: GunMapping) -> bool:
    # no gun, enable the cross for joysticks, mouses...
    if not guns:
        return True

    return any(gun.need_cross for gun in guns.values())


type GunMapping = Mapping[int, Gun]
type GunDict = dict[int, Gun]
