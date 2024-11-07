from __future__ import annotations

import logging
import math
import os
import re
import signal
import subprocess
from typing import TYPE_CHECKING, Final, cast

import evdev

from .. import controllersConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..controller import Controller, ControllerDict, ControllerMapping
    from ..Emulator import Emulator
    from ..types import DeviceInfoDict, DeviceInfoMapping

_logger = logging.getLogger(__name__)

_WHEEL_MAPPING: Final = {
    "wheel":      "joystick1left",
    "accelerate": "r2",
    "brake":      "l2",
    "downshift":  "pageup",
    "upshift":    "pagedown"
}

# partial mapping between real pads buttons and batocera pads
_EMULATOR_MAPPING: Final = {
    "dreamcast": {
        "lt":   "l2",
        "rt":   "r2",
        "up":   "pageup",
        "down": "pagedown"
    },
    "gamecube": {
        "lt": "l2",
        "rt": "r2",
        "a":  "a",
        "b":  "b",
        "x":  "x",
        "y":  "y"
    },
    "saturn": {
        "l":      "l2",
        "r":      "r2",
        "a":      "b",
        "b":      "a",
        "c":      "pagedown",
        "x":      "y",
        "y":      "x",
        "z":      "pageup",
        "start":  "start"
    },
    "n64": {
        "l":     "pageup",
        "r":     "pagedown",
        "a":     "b",
        "b":     "y",
        "start": "start"
    },
    "wii": {
        "lt": "l2",
        "rt": "r2",
        "a":  "a",
        "b":  "b",
        "x":  "x",
        "y":  "y"
    },
    "wiiu": {
        "a":      "a",
        "b":      "b",
        "x":      "x",
        "y":      "y",
        "start":  "start",
        "select": "select"
    },
    "psx": {
        "cross":    "b",
        "square":   "y",
        "round":    "a",
        "triangle": "x",
        "start":    "start",
        "select":    "select"
    },
    "ps2": {
        "cross":    "b",
        "square":   "y",
        "round":    "a",
        "triangle": "x"
    },
    "xbox": {
        "lt": "l2",
        "rt": "r2",
        "a":  "b",
        "b":  "a",
        "x":  "y",
        "y":  "x"
    },
}

def configure_wheels(
    controllers: ControllerMapping, system: Emulator, metadata: dict[str, str], /,
) -> tuple[list[subprocess.Popen[bytes]], ControllerDict, DeviceInfoDict]:
    devices = controllersConfig.getDevicesInformation()

    _logger.info("wheels reconfiguration")

    _logger.info("before wheel reconfiguration :")
    for player_number, pad in sorted(controllers.items()):
        _logger.info("  %s. index:%s dev:%s name:%s", player_number, pad.index, pad.device_path, pad.real_name)

    # reconfigure wheel buttons
    # no need to sort, but i like keeping the same loop (sorted by players)
    for _, pad in sorted(controllers.items()):
        if pad.device_path in devices and devices[pad.device_path]["isWheel"]:
            _logger.info("Wheel reconfiguration for pad %s", pad.real_name)
            original_inputs = pad.inputs.copy()

            # erase target keys
            for md_key, md_value in metadata.items():
                if md_key.startswith("wheel_"):
                    short_md_key = md_key[6:]
                    if (
                        (wheel_key := _WHEEL_MAPPING.get(short_md_key)) is not None and
                        md_value in _EMULATOR_MAPPING.get(system.name, {}) and
                        wheel_key in pad.inputs
                    ):
                        del pad.inputs[wheel_key]
                        _logger.info("wheel: erase the key %s", wheel_key)

            # fill with the wanted keys
            for md_key, md_value in metadata.items():
                if md_key.startswith("wheel_"):
                    short_md_key = md_key[6:]
                    if (
                        (wheel_key := _WHEEL_MAPPING.get(short_md_key)) is not None and
                        (wanted_key := _EMULATOR_MAPPING.get(system.name, {}).get(md_value)) is not None
                    ):
                        if wheel_key in original_inputs:
                            pad.inputs[wanted_key] = original_inputs[wheel_key]
                            pad.inputs[wanted_key].name = wanted_key
                            _logger.info("wheel: fill key %s with %s", wanted_key, wheel_key)
                        else:
                            _logger.info("wheel: unable to replace %s with %s", wanted_key, wheel_key)

    # reconfigure wheel min/max/deadzone
    procs: list[subprocess.Popen[bytes]] = []
    recompute_sdl_ids = False
    new_pads: set[str] = set()

    for player_number, pad in sorted(controllers.items()):
        if (device := devices.get(pad.device_path)) is not None and device["isWheel"] and "wheel_rotation" in device:
            ra = int(device["wheel_rotation"])
            wanted_ra = ra
            wanted_deadzone = 0
            wanted_midzone  = 0

            # initialize values with games metadata
            if "wheel_rotation" in metadata:
                wanted_ra = int(metadata["wheel_rotation"])
            if "wheel_deadzone" in metadata:
                wanted_deadzone = int(metadata["wheel_deadzone"])
            if "wheel_midzone" in metadata:
                wanted_midzone = int(metadata["wheel_midzone"])

            # override with user configs
            if "wheel_rotation" in system.config:
                wanted_ra = int(system.config["wheel_rotation"])
            if "wheel_deadzone" in system.config:
                wanted_deadzone = int(system.config["wheel_deadzone"])
            if "wheel_midzone" in system.config:
                wanted_midzone = int(system.config["wheel_midzone"])

            _logger.info("wheel rotation angle is %s ; wanted wheel rotation angle is %s ; wanted deadzone is %s ; wanted midzone is %s", ra, wanted_ra, wanted_deadzone, wanted_midzone)

            # no need new device in some cases
            if wanted_ra < ra or wanted_deadzone > 0:
                newdev, p = _reconfigure_angle_rotation(pad, ra, wanted_ra, wanted_deadzone, wanted_midzone)
                if newdev is not None:
                    _logger.info("replacing device %s by device %s for player %s", pad.device_path, newdev, player_number)
                    devices[newdev] = device.copy()
                    devices[newdev]["eventId"] = cast(int, controllersConfig.dev2int(newdev))
                    pad.physical_device_path = pad.device_path # save the physical device for ffb
                    pad.device_path = newdev # needs to recompute sdl ids
                    recompute_sdl_ids = True
                    new_pads.add(newdev)
                    procs.append(cast(subprocess.Popen[bytes], p))

    # recompute sdl ids
    if recompute_sdl_ids:
        # build the new joystick list
        joysticks: dict[int, str] = {}

        for node, device in devices.items():
            if device["isJoystick"]:
                joysticks[device["eventId"]] = node

        # add the new devices
        for pad_device_path in new_pads:
            matches = re.match(r"^/dev/input/event([0-9]*)$", pad_device_path)
            if matches is not None:
                joysticks[int(matches.group(1))] = pad_device_path

        # find new sdl numeration
        joysticks_by_dev: dict[str, int] = {}
        for current_id, (_, x) in enumerate(sorted(joysticks.items())):
            joysticks_by_dev[x] = current_id

        # renumeration
        for _, pad in sorted(controllers.items()):
            joystick_index = joysticks_by_dev.get(pad.device_path)
            if joystick_index is not None:
                pad.index = joystick_index
                devices[pad.device_path]["joystick_index"] = joystick_index

        # fill physical_index
        for _, pad in sorted(controllers.items()):
            if pad.physical_device_path is not None and (device := devices.get(pad.physical_device_path)) is not None and "joystick_index" in device:
                pad.physical_index = device["joystick_index"] # save the physical device for ffb

    # reorder players to priorize wheel pads
    controllers_new: ControllerDict = {}
    nplayer = 1
    for _, pad in sorted(controllers.items()):
        if (pad.device_path in devices and devices[pad.device_path]["isWheel"]) or pad.device_path in new_pads:
            controllers_new[nplayer] = pad.replace(player_number=nplayer)
            nplayer += 1

    for _, pad in sorted(controllers.items()):
        if not ((pad.device_path in devices and devices[pad.device_path]["isWheel"]) or pad.device_path in new_pads):
            controllers_new[nplayer] = pad.replace(player_number=nplayer)
            nplayer += 1

    _logger.info("after wheel reconfiguration :")
    for player_number, pad in sorted(controllers_new.items()):
        _logger.info("  %s. index:%s dev:%s name:%s", player_number, pad.index, pad.device_path, pad.real_name)

    return procs, controllers_new, _get_wheels_from_device_infos(devices)

def _get_wheels_from_device_infos(device_infos: DeviceInfoMapping, /) -> DeviceInfoDict:
    return { key: deviceInfo for key, deviceInfo in device_infos.items() if deviceInfo['isWheel']}

def _reconfigure_angle_rotation(controller: Controller, rotation_angle: int, wanted_rotation_angle: int, wanted_deadzone: int, wanted_midzone: int, /) -> tuple[str, subprocess.Popen[bytes]] | tuple[None, None]:
    wheel_axis = int(controller.inputs["joystick1left"].id)
    dev_infos = evdev.InputDevice(controller.device_path)
    caps = dev_infos.capabilities()

    abs_min = None
    abs_max = None
    for v, absinfo in caps[evdev.ecodes.EV_ABS]:
        if v == wheel_axis:
            abs_min = absinfo.min
            abs_max = absinfo.max

    if abs_min is None or abs_max is None:
        _logger.warning("unable to get min/max of %s", controller.device_path)
        return (None, None)

    total_range = abs_max - abs_min
    new_min = abs_min
    new_max = abs_max

    if wanted_rotation_angle < rotation_angle:
        new_range = math.floor(total_range * wanted_rotation_angle / rotation_angle)
        new_min = abs_min + math.ceil((total_range - new_range) / 2)
        new_max = abs_max - math.floor((total_range - new_range) / 2)

    new_deadzone = 0

    if wanted_deadzone > 0 and wanted_deadzone > wanted_midzone:
        new_deadzone = math.floor(total_range * wanted_deadzone / rotation_angle)
        new_min -= new_deadzone // 2
        new_max += new_deadzone // 2

    new_midzone = 0

    if wanted_midzone > 0:
        new_midzone = math.floor(total_range * wanted_midzone / rotation_angle)
        new_min += new_midzone // 2
        new_max -= new_midzone // 2

    pipe_out, pipe_in = os.pipe()
    cmd: list[str] = [
        "batocera-wheel-calibrator",
        "-d", controller.device_path,
        "-a", f"{wheel_axis}",
        "-m", f"{new_min}",
        "-M", f"{new_max}",
        "-z", f"{new_deadzone}",
        "-c", f"{new_midzone}"
    ]

    _logger.info(cmd)

    proc = subprocess.Popen(cmd, stdout=pipe_in, stderr=subprocess.PIPE)

    try:
        with os.fdopen(pipe_out) as fd:
            new_dev = fd.readline().rstrip('\n')
    except:
        os.kill(proc.pid, signal.SIGTERM)
        proc.communicate()
        raise

    return new_dev, proc

def reset_wheels(processes: Iterable[subprocess.Popen[bytes]], /) -> None:
    for p in processes:
        _logger.info("killing wheel process %s", p.pid)
        os.kill(p.pid, signal.SIGTERM)
        p.communicate()
