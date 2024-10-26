from __future__ import annotations

import logging
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, cast

import evdev

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

def _get_mouse_buttons(device: evdev.InputDevice) -> list[str]:
    caps_keys = device.capabilities()[evdev.ecodes.EV_KEY]
    mouse_caps = set(caps_keys) & set(_mouse_code_to_button.keys())

    return [button for cap, button in _mouse_code_to_button.values() if cap in mouse_caps]


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


def gun_button_to_code(button: str) -> int | None:
    return _mouse_button_to_code.get(button)


def guns_need_crosses(guns: GunMapping) -> bool:
    # no gun, enable the cross for joysticks, mouses...
    if not guns:
        return True

    return any(gun.need_cross for gun in guns.values())

def guns_borders_size_name(guns: GunMapping, config: Mapping[str, object]) -> str | None:
    borders_size: str = cast(str, config.get("controllers.guns.borderssize", "medium"))

    # overriden by specific options
    borders_mode = "normal"
    if (config_borders_mode := cast(str, config.get("controllers.guns.bordersmode", "auto"))) != "auto":
        borders_mode = config_borders_mode
    if (config_borders_mode := cast(str, config.get("bordersmode", "auto"))) != "auto":
        borders_mode = config_borders_mode

    # others are gameonly and normal
    if borders_mode == "hidden":
        return None

    if borders_mode == "force":
        return borders_size

    for gun in guns.values():
        if gun.need_borders:
            return borders_size

    return None

# returns None to follow the bezel overlay size by default
def guns_border_ratio_type(guns: GunMapping, config: dict[str, str]) -> str | None:
    if "controllers.guns.bordersratio" in config:
        return config["controllers.guns.bordersratio"] # "4:3"
    return None


type GunMapping = Mapping[int, Gun]
type GunDict = dict[int, Gun]
