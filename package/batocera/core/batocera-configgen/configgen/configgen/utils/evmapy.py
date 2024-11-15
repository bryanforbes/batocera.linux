from __future__ import annotations

import json
import logging
import re
import subprocess
from collections import defaultdict
from contextlib import AbstractContextManager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, NotRequired, TypedDict, cast

import evdev

from ..batoceraPaths import CONFIGS, EVMAPY
from ..gun import Gun, GunMapping, gun_button_to_code

if TYPE_CHECKING:
    from collections.abc import Container, Mapping
    from types import TracebackType

    from ..controller import Controller, ControllerMapping


_logger = logging.getLogger(__name__)

_EVMAPY_SHARE_DIR: Final = Path('/usr/share/evmapy')
_EVMAPY_RUN_DIR: Final = Path('/var/run/evmapy')


class _EvmapyAction(TypedDict):
    trigger: str | list[str]
    type: Literal['exec', 'key', 'mouse']
    target: str | list[str]
    mode: NotRequired[Literal['all', 'sequence', 'any']]
    hold: NotRequired[float]


class _EvmapyButton(TypedDict):
    name: str
    code: int


class _EvmapyAxis(_EvmapyButton):
    min: float
    max: float


class _EvmapyConfig(TypedDict):
    actions: list[_EvmapyAction]
    grab: bool
    axes: NotRequired[list[_EvmapyAxis]]
    buttons: NotRequired[list[_EvmapyButton]]


class _KeysActionBase(TypedDict):
    trigger: str | list[str]
    mode: NotRequired[Literal['all', 'sequence', 'any']]
    hold: NotRequired[float]
    description: NotRequired[str]


class _KeysAction(_KeysActionBase):
    type: Literal['exec', 'key']
    target: str | list[str]


class _KeysMouseAction(_KeysActionBase):
    type: Literal['mouse']


type _KeysActions = list[_KeysAction | _KeysMouseAction]
type _KeysConfig = dict[str, _KeysActions]


def _keys_action_to_evmapy_action(keys_action: _KeysAction, /) -> _EvmapyAction:
    return cast(_EvmapyAction, {key: value for key, value in keys_action.items() if key != 'description'})


_gun_re = re.compile(r'^actions_gun(\d+)$')
_player_re = re.compile(r'^actions_player(\d+)$')


@dataclass(slots=True)
class evmapy(AbstractContextManager[None, None]):
    # evmapy is a process that map pads to keyboards (for pygame for example)
    __started: bool = field(init=False, default=False)

    system: str
    emulator: str
    core: str
    rom: Path
    controllers: ControllerMapping
    guns: GunMapping

    def __enter__(self) -> None:
        if self.__prepare():
            self.__started = True
            subprocess.call(["batocera-evmapy", "start"])

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None:
        if self.__started:
            self.__started = False
            subprocess.call(["batocera-evmapy", "stop"])

    def __build_merged_keys_file(self) -> Path | None:
        # consider files here in this order to get a configuration
        files_to_merge: list[Path] = [
            # {rom}.keys form is forbidden for directories, it must be inside
            (self.rom.parent / f"{self.rom.name}.keys") if not self.rom.is_dir() else (self.rom / 'padto.keys'),
            # EVMAPY / f"{self.system}.{self.emulator}.{self.core}.keys",
            # EVMAPY / f"{self.system}.{self.emulator}.keys",
            EVMAPY / f"{self.system}.keys" ,
            EVMAPY / f"{self.emulator}.keys" ,
            EVMAPY / "any.keys",
            # _EVMAPY_SHARE_DIR / f"{self.system}.{self.emulator}.{self.core}.keys" ,
            _EVMAPY_SHARE_DIR / f"{self.system}.{self.emulator}.keys" ,
            _EVMAPY_SHARE_DIR / f"{self.system}.keys" ,
            _EVMAPY_SHARE_DIR / f"{self.emulator}.keys" ,
            _EVMAPY_SHARE_DIR / "any.keys",
        ]
        files_to_merge = [keys_file for keys_file in files_to_merge if keys_file.exists()]

        # merge conditionnally on the global hotkeys file until it is set everywhere
        keysfile     = _EVMAPY_SHARE_DIR / "hotkeys.keys"
        userkeysfile = CONFIGS / "hotkeys.keys" # prefer the custom one
        if userkeysfile.exists():
            keysfile = userkeysfile

        if keysfile.exists():
            _logger.debug("evmapy file to merge for hotkeys : %s", keysfile)
            files_to_merge.append(keysfile)

        if not files_to_merge:
            _logger.debug("no files to merge")
            return None

        _logger.debug("files to merge : %s", files_to_merge)

        if len(files_to_merge) == 1:
            return files_to_merge[0]

        merged_unique_values: dict[str, dict[str, _KeysAction | _KeysMouseAction]] = defaultdict(dict)

        for file in files_to_merge:
            with file.open() as f:
                values: _KeysConfig = json.load(f)

            for player_actions, player_actions_values in values.items():
                for action in player_actions_values:
                    #merge multiple trigger keys list in a single ordered key
                    if isinstance(action['trigger'], list):
                        action['trigger'].sort()
                        trigger = "-".join(action['trigger'])
                    else:
                        trigger = action['trigger']
                    if trigger not in merged_unique_values[player_actions]:
                        merged_unique_values[player_actions][trigger] = action

        merged_values: _KeysConfig = defaultdict(list)

        for player_actions, player_actions_value in merged_unique_values.items():
            for _, value in player_actions_value.items():
                merged_values[player_actions].append(value)

        merged_file = Path("/var/run/evmapy_merged.keys")

        with merged_file.open("w") as fd:
            fd.write(json.dumps(merged_values, indent=2))

        return merged_file

    def __write_gun_config(self, gun: Gun, actions: _KeysActions, keys_file: Path, /) -> None:
        configfile = _EVMAPY_RUN_DIR / f"{Path(gun.node).name}.json"
        _logger.debug("config file for keysfile is %s (from %s) - gun" , configfile, keys_file)

        evmapy_config: _EvmapyConfig = {
            'buttons': [],
            'axes': [],
            'actions': [],
            'grab': False
        }

        for button in gun.buttons:
            evmapy_config['buttons'].append({
                'name': button,
                'code': cast(int, gun_button_to_code(button))
            })

        for action in actions:
            if 'trigger' in action and 'type' in 'action' and 'target' in action:
                gun_trigger = self.__get_gun_trigger(action['trigger'], gun)
                if gun_trigger:
                    evmapy_action = _keys_action_to_evmapy_action(action)
                    evmapy_action['trigger'] = gun_trigger
                    evmapy_config['actions'].append(evmapy_action)

        with configfile.open('w') as fd:
            json.dump(evmapy_config, fd, indent=2)

    def __write_controller_config(self, controller: Controller, keys_actions: _KeysActions, keys_file: Path, /) -> None:
        configfile = _EVMAPY_RUN_DIR / f'{Path(controller.device_path).name}.json'
        _logger.debug("config file for keysfile is %s (from %s)" , configfile, keys_file)

        # create mapping
        evmapy_config: _EvmapyConfig = {
            'actions': [],
            'axes': [],
            'buttons': [],
            'grab': False,
        }

        absbasex_positive = True
        absbasey_positive = True

        # define buttons / axes
        known_button_names: set[str] = set()
        known_button_codes: dict[str, str] = {}
        known_button_aliases: dict[str, str] = {}
        known_axis_codes: set[str] = set()

        for input in controller.inputs.values():
            if input.type == 'button':
                # don't add the same button twice (ie select as hotkey)
                if input.code is not None:
                    if input.code not in known_button_codes:
                        known_button_names.add(input.name)
                        known_button_codes[input.code] = input.name  # keep the master name for aliases
                        evmapy_config["buttons"].append({
                            "name": input.name,
                            "code": int(input.code)
                        })
                    else:
                        known_button_aliases[input.name] = known_button_codes[input.code]
            elif input.type == "hat":
                if (input_value := int(input.value)) in [1, 2]:  # don't duplicate values
                    if input_value == 1:
                        name = "X"
                        is_y_as_int = 0
                    else:
                        name = "Y"
                        is_y_as_int =  1

                    known_button_names.add(f"HAT{input.id}{name}:min")
                    known_button_names.add(f"HAT{input.id}{name}:max")

                    evmapy_config["axes"].append({
                        "name": f"HAT{input.id}{name}",
                        "code": int(input.id) + 16 + is_y_as_int, # 16 = HAT0X in linux/input.h
                        "min": -1,
                        "max": 1
                    })
            elif input.type == "axis":  # noqa: SIM102
                if input.code not in known_axis_codes:
                    # avoid duplicated value for axis (bad pad configuration that make evmappy to stop)
                    known_axis_codes.add(cast(str, input.code))

                    axis_id: str | None = None
                    axis_name: str | None = None

                    if input.name == "joystick1up" or input.name == "joystick1left":
                        axis_id = "0"
                    elif input.name == "joystick2up" or input.name == "joystick2left":
                        axis_id = "1"
                    if input.name == "joystick1up" or input.name == "joystick2up":
                        axis_name = "Y"
                    elif input.name == "joystick1left" or input.name == "joystick2left":
                        axis_name = "X"
                    elif input.name == "up" or input.name == "down":
                        axis_id   = "BASE"
                        axis_name = "Y"
                        if input.name == "up":
                            absbasey_positive =  int(input.value) >= 0
                        else:
                            axis_id = None # don't duplicate, configuration should be done for up
                    elif input.name == "left" or input.name == "right":
                        axis_id   = "BASE"
                        axis_name = "X"
                        if input.name == "left":
                            absbasex_positive = int(input.value) < 0
                        else:
                            axis_id = None # don't duplicate, configuration should be done for left
                    else:
                        axis_id   = "_OTHERS_"
                        axis_name = input.name

                    if (
                        ((axis_id in ["0", "1", "BASE"] and axis_name in ["X", "Y"]) or axis_id == "_OTHERS_") and
                        input.code is not None
                    ):
                        axis_min, axis_max = self.__get_pad_min_max_axis(controller.device_path, int(input.code))
                        known_button_names.add(f"ABS{axis_id}{axis_name}:min")
                        known_button_names.add(f"ABS{axis_id}{axis_name}:max")
                        known_button_names.add(f"ABS{axis_id}{axis_name}:val")

                        evmapy_config["axes"].append({
                            "name": "ABS" + axis_id + axis_name,
                            "code": int(input.code),
                            "min": axis_min,
                            "max": axis_max
                        })

        axis_for_mouse: set[str] = set()
        trigger_mapping = self.__get_mapping_for_triggers(known_button_names, absbasex_positive, absbasey_positive)

        for keys_action in keys_actions:
            evmapy_action: _EvmapyAction | None = None

            # handle mouse events : only joystick1 or joystick2 defined for 2 events
            if (
                "type" in keys_action and
                keys_action["type"] == "mouse" and
                "target" not in keys_action and
                "trigger" in keys_action
            ):
                if keys_action["trigger"] == "joystick1":
                    evmapy_action = {
                        **keys_action,
                        'trigger': 'joystick1x',
                        'target': 'X',
                    }
                    evmapy_action = {
                        **keys_action,
                        'trigger': 'joystick1y',
                        'target': 'Y',
                    }
                elif keys_action["trigger"] == "joystick2":
                    evmapy_action = {
                        **keys_action,
                        'trigger': 'joystick2x',
                        'target': 'X',
                    }
                    evmapy_action = {
                        **keys_action,
                        'trigger': 'joystick2y',
                        'target': 'Y',
                    }
            else:
                evmapy_action = _keys_action_to_evmapy_action(keys_action)

            if evmapy_action is None:
                continue

            # only add actions for which buttons are defined (otherwise, evmapy doesn't like it)
            if 'trigger' in evmapy_action:
                trigger = self.__trigger_mapper(
                    evmapy_action["trigger"],
                    known_button_aliases,
                    known_button_names,
                    trigger_mapping,
                )
                if "mode" not in evmapy_action:
                    mode = self.__trigger_mapper_mode(evmapy_action["trigger"])
                    if mode is not None:
                        evmapy_action["mode"] = mode

                evmapy_action['trigger'] = trigger

                if isinstance(trigger, list):
                    if all(x in known_button_names or f"ABS_OTHERS_{x}:max" in known_button_names for x in trigger):
                        # rewrite axis buttons
                        for x, val in enumerate(trigger):
                            if f"ABS_OTHERS_{val}:max" in known_button_names:
                                trigger[x] = f"ABS_OTHERS_{val}:max"
                        evmapy_config['actions'].append(evmapy_action)
                else:
                    if trigger in known_button_names:
                        evmapy_config['actions'].append(evmapy_action)
                    if f"ABS_OTHERS_{trigger}:max" in known_button_names:
                        evmapy_action["trigger"] = f"ABS_OTHERS_{evmapy_action['trigger']}:max"
                        evmapy_config['actions'].append(evmapy_action)

            if "type" in evmapy_action and evmapy_action["type"] == "mouse":
                if isinstance(evmapy_action["trigger"], list):
                    for x in evmapy_action["trigger"]:
                        axis_for_mouse.add(x)
                else:
                    axis_for_mouse.add(evmapy_action["trigger"])

        # use full axis for mouse and 50% for keys
        for axis in evmapy_config["axes"]:
            if (
                f'{axis["name"]}:val' not in axis_for_mouse and
                f'{axis["name"]}:min' not in axis_for_mouse and
                f'{axis["name"]}:max' not in axis_for_mouse
            ):
                axis["min"], axis["max"] = self.__get_pad_min_max_axis_for_keys(axis["min"], axis["max"])

        # save config file
        with configfile.open("w") as fd:
            json.dump(evmapy_config, fd, indent=2)

    def __prepare(self) -> bool:
        keys_file = self.__build_merged_keys_file()

        if keys_file is None:
            # otherwise, preparation did nothing
            _logger.debug("no evmapy config file found for system=%s, emulator=%s", self.system, self.emulator)
            return False

        _logger.debug("evmapy on %s", keys_file)
        subprocess.call(["batocera-evmapy", "clear"])

        with keys_file.open() as f:
            keys_config: _KeysConfig = json.load(f)

        for key, actions in keys_config.items():
            if (match := _gun_re.match(key)) is not None and (gun := self.guns.get(int(match.group(1)))) is not None:
                self.__write_gun_config(gun, actions, keys_file)
            elif (match := _player_re.match(key)) is not None and (controller := self.controllers.get(int(match.group(1)))) is not None:
                self.__write_controller_config(controller, actions, keys_file)

        return True

    def __get_mapping_for_triggers(
        self,
        known_button_names: Container[str],
        absbasex_positive: bool,
        absbasey_positive: bool,
        /,
    ):
        # maybe this function is more complex if a pad has several hat. never see them.
        mapping: dict[str, str | list[str]] = {
            "joystick1right": "ABS0X:max",
            "joystick1left": "ABS0X:min",
            "joystick1down": "ABS0Y:max",
            "joystick1up": "ABS0Y:min",
            "joystick2right": "ABS1X:max",
            "joystick2left": "ABS1X:min",
            "joystick2down": "ABS1Y:max",
            "joystick2up": "ABS1Y:min",
            "joystick1x": ["ABS0X:val", "ABS0X:min", "ABS0X:max"],
            "joystick1y": ["ABS0Y:val", "ABS0Y:min", "ABS0Y:max"],
            "joystick2x": ["ABS1X:val", "ABS1X:min", "ABS1X:max"],
            "joystick2y": ["ABS1Y:val", "ABS1Y:min", "ABS1Y:max"]
        }

        if "HAT0X:min" in known_button_names:
            mapping["left"]  = "HAT0X:min"
            mapping["right"] = "HAT0X:max"
            mapping["down"]  = "HAT0Y:max"
            mapping["up"]    = "HAT0Y:min"

        if "ABSBASEX:min" in known_button_names:
            if absbasex_positive:
                mapping["left"]  = "ABSBASEX:min"
                mapping["right"] = "ABSBASEX:max"
            else:
                mapping["left"]  = "ABSBASEX:max"
                mapping["right"] = "ABSBASEX:min"

        if "ABSBASEX:min" in known_button_names:
            if absbasey_positive:
                mapping["down"]  = "ABSBASEY:max"
                mapping["up"]    = "ABSBASEY:min"
            else:
                mapping["down"]  = "ABSBASEY:min"
                mapping["up"]    = "ABSBASEY:max"

        return mapping

    # remap evmapy trigger (aka up become HAT0Y:max)
    def __trigger_mapper(
        self,
        trigger: str | list[str],
        known_button_aliases: Mapping[str, str],
        known_button_names: Container[str],
        trigger_mapping: Mapping[str, str | list[str]],
        /,
    ) -> str | list[str]:
        if isinstance(trigger, list):
            return [
                cast(str, self.__trigger_mapper_string(x, known_button_aliases, known_button_names, trigger_mapping))
                for x in trigger
            ]

        return self.__trigger_mapper_string(trigger, known_button_aliases, known_button_names, trigger_mapping)

    def __trigger_mapper_string(
        self,
        trigger: str,
        known_button_aliases: Mapping[str, str],
        known_button_names: Container[str],
        trigger_mapping: Mapping[str, str | list[str]],
        /,
    ) -> str | list[str]:
        if trigger in known_button_aliases:
            return known_button_aliases[trigger]

        if (mapped := trigger_mapping.get(trigger)) is not None:
            if isinstance(mapped, list):
                if all(x in known_button_names for x in mapped):
                    return mapped
            elif mapped in known_button_names:
                return mapped

        return trigger # no tranformation

    def __trigger_mapper_mode(self, trigger: str | list[str], /) -> Literal['all', 'sequence', 'any'] | None:
        if isinstance(trigger, list):
            for x in trigger:
                mode = self.__trigger_mapper_mode_string(x)
                if mode is not None:
                    return mode
            return None
        return self.__trigger_mapper_mode_string(trigger)

    def __trigger_mapper_mode_string(self, trigger: str, /):
        if trigger in [ "joystick1x", "joystick1y", "joystick2x", "joystick2y"]:
            return "any"
        return None

    def __get_gun_trigger(self, trigger: str | list[str], gun: Gun, /) -> str | list[str] | None:
        if isinstance(trigger, list):
            for button in trigger:
                if button not in gun.buttons:
                    return None
            return trigger
        else:
            if trigger not in gun.buttons:
                return None
            return trigger

    def __get_pad_min_max_axis(self, device_path: str, axis_code: int, /) -> tuple[int, int]:
        device = evdev.InputDevice(device_path)
        capabilities = device.capabilities(False)

        for event_type, event_capability in capabilities.items():
            if event_type == 3: # "EV_ABS"
                for abs_code, val in cast(list[tuple[int, evdev.AbsInfo]], event_capability):
                    if abs_code == axis_code:
                        return val.min, val.max
        return 0, 0  # not found

    def __get_pad_min_max_axis_for_keys(self, min: float, max: float, /) -> tuple[float, float]:
        mid_point = (max - min) / 2  # for each side
        new_min   = min + mid_point / 2
        new_max   = max - mid_point / 2
        return new_min, new_max
