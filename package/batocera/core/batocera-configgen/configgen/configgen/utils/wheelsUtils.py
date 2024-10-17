from __future__ import annotations

import logging
import math
import os
import re
import signal
import subprocess
from typing import TYPE_CHECKING, cast

import evdev

from .. import controllersConfig

if TYPE_CHECKING:
    from collections.abc import Iterable

    from ..controller import Controller, ControllerPlayerDict, ControllerPlayerMapping
    from ..Emulator import Emulator
    from ..types import DeviceInfoDict, DeviceInfoMapping

eslog = logging.getLogger(__name__)

wheelMapping = {
    "wheel":      "joystick1left",
    "accelerate": "r2",
    "brake":      "l2",
    "downshift":  "pageup",
    "upshift":    "pagedown"
}

# partial mapping between real pads buttons and batocera pads
emulatorMapping = {
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
    controllers: ControllerPlayerMapping,
    system: Emulator,
    metadata: dict[str, str],
    /,
) -> tuple[list[subprocess.Popen[bytes]], ControllerPlayerDict, DeviceInfoDict]:
    devices = controllersConfig.getDevicesInformation()

    eslog.info("wheels reconfiguration")

    eslog.info("before wheel reconfiguration :")
    for playercontroller, pad in sorted(controllers.items()):
        eslog.info(f"  {playercontroller}. index:{pad.index!s} dev:{pad.device_path} name:{pad.real_name}")

    # reconfigure wheel buttons
    # no need to sort, but i like keeping the same loop (sorted by players)
    for _, pad in sorted(controllers.items()):
        if pad.device_path in devices:
            if devices[pad.device_path]['isWheel']:
                eslog.info(f"Wheel reconfiguration for pad {pad.real_name}")
                originalInputs = pad.inputs.copy()

                # erase target keys
                for md_key, md_value in metadata.items():
                    if md_key.startswith('wheel_'):
                        shortmd = md_key[6:]
                        if shortmd in wheelMapping:
                            if system.name in emulatorMapping and md_value in emulatorMapping[system.name]:
                                wheelkey  = wheelMapping[shortmd]
                                if wheelkey in pad.inputs:
                                    del pad.inputs[wheelkey]
                                    eslog.info(f"wheel: erase the key {wheelkey}")

                # fill with the wanted keys
                for md_key, md_value in metadata.items():
                    if md_key.startswith('wheel_'):
                        shortmd = md_key[6:]
                        if shortmd in wheelMapping:
                            if system.name in emulatorMapping and md_value in emulatorMapping[system.name]:
                                wheelkey  = wheelMapping[shortmd]
                                wantedkey = emulatorMapping[system.name][md_value]

                                if wheelkey in originalInputs:
                                    pad.inputs[wantedkey] = originalInputs[wheelkey]
                                    pad.inputs[wantedkey].name = wantedkey
                                    eslog.info(f"wheel: fill key {wantedkey} with {wheelkey}")
                                else:
                                    eslog.info(f"wheel: unable to replace {wantedkey} with {wheelkey}")

    # reconfigure wheel min/max/deadzone
    procs: list[subprocess.Popen[bytes]] = []
    recomputeSdlIds = False
    newPads: list[str] = []

    for playercontroller, pad in sorted(controllers.items()):
        device = devices.get(pad.device_path) if pad.device_path is not None else None
        if device is not None and device["isWheel"] and "wheel_rotation" in device:
            ra = int(device['wheel_rotation'])
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

            eslog.info(f"wheel rotation angle is {ra} ; wanted wheel rotation angle is {wanted_ra} ; wanted deadzone is {wanted_deadzone} ; wanted midzone is {wanted_midzone}")

            # no need new device in some cases
            if wanted_ra < ra or wanted_deadzone > 0:
                newdev, p = _reconfigure_angle_rotation(pad, ra, wanted_ra, wanted_deadzone, wanted_midzone)
                if newdev is not None:
                    eslog.info(f"replacing device {pad.device_path} by device {newdev} for player {playercontroller}")
                    devices[newdev] = device.copy()
                    devices[newdev]['eventId'] = cast(int, controllersConfig.dev2int(newdev))
                    pad.physical_device_path = pad.device_path  # save the physical device for ffb
                    pad.device_path = newdev  # needs to recompute sdl ids
                    recomputeSdlIds = True
                    newPads.append(newdev)
                    procs.append(cast(subprocess.Popen[bytes], p))

    # recompute sdl ids
    if recomputeSdlIds:
        # build the new joystick list
        joysticks: dict[int, str] = {}

        for node, device in devices.items():
            if device["isJoystick"]:
                joysticks[device["eventId"]] = node

        # add the new devices
        for pad_device_path in newPads:
            matches = re.match(r"^/dev/input/event([0-9]*)$", pad_device_path)
            if matches is not None:
                joysticks[int(matches.group(1))] = pad_device_path

        # find new sdl numeration
        joysticks_by_dev: dict[str, int] = {}
        for current_id, (_, x) in enumerate(sorted(joysticks.items())):
            joysticks_by_dev[x] = current_id

        # renumeration
        for _, pad in sorted(controllers.items()):
            if pad.device_path in joysticks_by_dev:
                pad.index = joysticks_by_dev[pad.device_path]
                devices[pad.device_path]["joystick_index"] = joysticks_by_dev[pad.device_path]

        # fill physical_id
        for _, pad in sorted(controllers.items()):
            if pad.physical_device_path is not None and (device := devices.get(pad.physical_device_path)) is not None and "joystick_index" in device:
                pad.physical_id = device["joystick_index"]  # save the physical device for ffb

    controllers_new: ControllerPlayerDict = {}
    nplayer = 1

    for _, pad in sorted(controllers.items()):
        if (pad.device_path in devices and devices[pad.device_path]['isWheel']) or pad.device_path in newPads:
            controllers_new[nplayer] = pad.replace(player=nplayer)
            nplayer += 1

    for _, pad in sorted(controllers.items()):
        if not ((pad.device_path in devices and devices[pad.device_path]['isWheel']) or pad.device_path in newPads):
            controllers_new[nplayer] = pad.replace(player=nplayer)
            nplayer += 1

    eslog.info("after wheel reconfiguration :")
    for playercontroller, pad in sorted(controllers_new.items()):
        eslog.info(f"  {playercontroller}. index:{pad.index!s} dev:{pad.device_path} name:{pad.real_name}")

    return procs, controllers_new, getWheelsFromDevicesInfos(devices)

def getWheelsFromDevicesInfos(deviceInfos: DeviceInfoMapping) -> DeviceInfoDict:
    return { key: deviceInfo for key, deviceInfo in deviceInfos.items() if deviceInfo['isWheel']}

def _reconfigure_angle_rotation(
    controller: Controller,
    rotationAngle: int,
    wantedRotationAngle: int,
    wantedDeadzone: int,
    wantedMidzone: int,
    /,
) -> tuple[str, subprocess.Popen[bytes]] | tuple[None, None]:
    wheelAxis = int(controller.inputs["joystick1left"].id)
    devInfos = evdev.InputDevice(cast(str, controller.device_path))
    caps = devInfos.capabilities()

    absmin = None
    absmax = None
    for v, absinfo in cast(list[tuple[int, evdev.AbsInfo]], caps[evdev.ecodes.EV_ABS]):
        if v == wheelAxis:
            absmin = absinfo.min
            absmax = absinfo.max

    if absmin is None or absmax is None:
        eslog.warning(f"unable to get min/max of {controller.device_path}")
        return (None, None)

    totalRange = absmax - absmin
    newmin = absmin
    newmax = absmax

    if wantedRotationAngle < rotationAngle:
        newRange = math.floor(totalRange * wantedRotationAngle / rotationAngle)
        newmin = absmin + math.ceil((totalRange - newRange) / 2)
        newmax = absmax - math.floor((totalRange - newRange) / 2)

    newdz = 0

    if wantedDeadzone > 0 and wantedDeadzone > wantedMidzone:
        newdz = math.floor(totalRange * wantedDeadzone / rotationAngle)
        newmin -= newdz // 2
        newmax += newdz // 2

    newmz = 0

    if wantedMidzone > 0:
        newmz = math.floor(totalRange * wantedMidzone / rotationAngle)
        newmin += newmz // 2
        newmax -= newmz // 2

    pipeout, pipein = os.pipe()
    cmd: list[str] = [
        "batocera-wheel-calibrator",
        "-d", f"{controller.device_path}",
        "-a", f"{wheelAxis}",
        "-m", f"{newmin}",
        "-M", f"{newmax}",
        "-z", f"{newdz}",
        "-c", f"{newmz}",
    ]
    eslog.info(cmd)
    proc = subprocess.Popen(cmd, stdout=pipein, stderr=subprocess.PIPE)

    try:
        with os.fdopen(pipeout) as fd:
            newdev = fd.readline().rstrip('\n')
    except:
        os.kill(proc.pid, signal.SIGTERM)
        proc.communicate()
        raise

    return newdev, proc

def resetControllers(wheelProcesses: Iterable[subprocess.Popen[bytes]]) -> None:
    for p in wheelProcesses:
        eslog.info(f"killing wheel process {p.pid}")
        os.kill(p.pid, signal.SIGTERM)
        out, err = p.communicate()
