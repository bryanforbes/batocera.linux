from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Literal, TypedDict, cast
from xml.dom import minidom

import toml

from .mupenPaths import (
    MUPEN_SYSTEM_MAPPING_TOML,
    MUPEN_USER_MAPPING_TOML,
    MUPEN_USER_MAPPING_XML,
)

if TYPE_CHECKING:

    from ...controller import Controller, Controllers
    from ...Emulator import Emulator
    from ...input import Input, InputMapping
    from ...types import DeviceInfoMapping
    from ...utils.configparser import CaseSensitiveConfigParser

# Must read :
# http://mupen64plus.org/wiki/index.php?title=Mupen64Plus_Plugin_Parameters

# Mupen doesn't like to have 2 buttons mapped for N64 pad entry. That's why r2 is commented for now. 1 axis and 1 button is ok
mupenHatToAxis        = {'1': 'Up',   '2': 'Right', '4': 'Down', '8': 'Left'}
mupenHatToReverseAxis = {'1': 'Down', '2': 'Left',  '4': 'Up',   '8': 'Right'}
mupenDoubleAxis = {0:'X Axis', 1:'Y Axis'}

valid_n64_controller_guids = [
    # official nintendo switch n64 controller
    "050000007e0500001920000001800000",
    # 8bitdo n64 modkit
    "05000000c82d00006928000000010000",
    "030000007e0500001920000011810000",
]

valid_n64_controller_names = [
    "N64 Controller",
    "Nintendo Co., Ltd. N64 Controller",
    "8BitDo N64 Modkit",
]


class _MupenInputConfig(TypedDict):
    AnalogDeadzone: str
    AnalogPeak: str
    inputs: dict[str, str]


class _MupenInputConfigs(TypedDict):
    retropad: _MupenInputConfig
    n64: _MupenInputConfig


def _convert_mupen_user_config_xml_to_toml() -> None:
    if MUPEN_USER_MAPPING_XML.exists():
        user_config: dict[str, dict[str, Any]] = defaultdict(defaultdict)

        dom = minidom.parse(str(MUPEN_USER_MAPPING_XML))
        for tag_name in ['defaultInputList', 'n64InputList']:
            for tag in dom.getElementsByTagName(tag_name):
                section = user_config['retropad' if tag_name == 'defaultInputList' else 'n64']
                for input in tag.childNodes:
                    if input.attributes and (name := input.attributes['name']) and (value := input.attributes['value']):
                        if name == 'AnalogDeadzone' or name == 'AnalogPeak':
                            section[name] = value
                        else:
                            section['inputs'][name] = value


def _merge_input_config(
    system_configs: _MupenInputConfigs, user_configs: dict[str, dict[str, Any]], config_name: Literal['retropad', 'n64'], /
) -> _MupenInputConfig:
    system_config = system_configs[config_name]
    user_config = user_configs.get(config_name, {})

    return {
        'AnalogDeadzone': user_config.get('AnalogDeadzone', system_config['AnalogDeadzone']),
        'AnalogPeak': user_config.get('AnalogPeak', system_config['AnalogPeak']),
        'inputs': {
            **system_config['inputs'],
            **user_config.get('inputs', {}),
        },
    }


def _load_mupen_input_configs() -> _MupenInputConfigs:
    input_config = cast(_MupenInputConfigs, toml.loads(MUPEN_SYSTEM_MAPPING_TOML.read_text()))

    if MUPEN_USER_MAPPING_TOML.exists():
        user_config = toml.loads(MUPEN_USER_MAPPING_TOML.read_text())

        return {
            'retropad': _merge_input_config(input_config, user_config, 'retropad'),
            'n64': _merge_input_config(input_config, user_config, 'n64')
        }

    return input_config


def setControllersConfig(iniConfig: CaseSensitiveConfigParser, controllers: Controllers, system: Emulator, wheels: DeviceInfoMapping) -> None:
    _convert_mupen_user_config_xml_to_toml()
    mupen_input_configs = _load_mupen_input_configs()

    for pad in controllers:
        isWheel = False
        if pad.device_path in wheels and wheels[pad.device_path]["isWheel"]:
            isWheel = True
        config = defineControllerKeys(pad.player_number, pad, system, isWheel, mupen_input_configs)
        fillIniPlayer(pad.player_number, iniConfig, pad, config)

    # remove section with no player
    for x in range(len(controllers) + 1, 4):
        section = f"Input-SDL-Control{x}"
        if iniConfig.has_section(section):
            cleanPlayer(x, iniConfig)

def getJoystickPeak(start_value: str, config_value: str, system: Emulator) -> str:
    default_value = int(start_value.split(',')[0])
    multiplier = system.config.get_float(config_value, 1)

    # This is needed because higher peak value lowers sensitivity and vice versa
    if multiplier != 1.0:
        adjusted_value = default_value * multiplier
        difference = abs(adjusted_value - default_value)

        # Figure out if we need to add or subtract the starting peak value
        if adjusted_value < default_value:
            peak = int(round(default_value + difference))
        else:
            peak = int(round(default_value - difference))
    else:
        peak = default_value

    return f"{peak},{peak}"

def getJoystickDeadzone(default_peak: str, config_value: str, system: Emulator) -> str:
    default_value = int(default_peak.split(',')[0])
    deadzone_multiplier = system.config.get_float(config_value, 0.01)

    deadzone = int(round(default_value * deadzone_multiplier))

    return f"{deadzone},{deadzone}"

def defineControllerKeys(nplayer: int, controller: Controller, system: Emulator, isWheel: bool, mupen_input_configs: _MupenInputConfigs) -> dict[str, str]:
        # check for auto-config inputs by guid and name, or es settings
        if (controller.guid in valid_n64_controller_guids and controller.name in valid_n64_controller_names) or (system.config.get(f"mupen64-controller{nplayer}", "retropad") != "retropad"):
            input_config = deepcopy(mupen_input_configs['n64'])
        else:
            input_config = deepcopy(mupen_input_configs['retropad'])

        mupeninputs = input_config["inputs"]

        # config holds the final pad configuration in the mupen style
        # ex: config['DPad U'] = "button(1)"
        config: dict[str, str] = {}

        # determine joystick deadzone and peak
        config['AnalogPeak'] = getJoystickPeak(input_config['AnalogPeak'], f"mupen64-sensitivity{nplayer}", system)

        # Analog Deadzone
        if isWheel:
            config['AnalogDeadzone'] = "0,0"
        else:
            config['AnalogDeadzone'] = getJoystickDeadzone(input_config['AnalogPeak'], f"mupen64-deadzone{nplayer}", system)

        # z is important, in case l2 is not available for this pad, use l1
        # assume that l2 is for "Z Trig" in the mapping
        if 'l2' not in controller.inputs:
            mupeninputs['pageup'] = mupeninputs['l2']

        # if joystick1up is not available, use up/left while these keys are more used
        if 'joystick1up' not in controller.inputs:
            mupeninputs['up']    = mupeninputs['joystick1up']
            mupeninputs['down']  = mupeninputs['joystick1down']
            mupeninputs['left']  = mupeninputs['joystick1left']
            mupeninputs['right'] = mupeninputs['joystick1right']

        # the input.xml adds 2 directions per joystick, ES handles just 1
        fakeSticks = { 'joystick2up' : 'joystick2down', 'joystick2left' : 'joystick2right'}
        # Cheat on the controller
        for realStick, fakeStick in fakeSticks.items():
                if realStick in controller.inputs and controller.inputs[realStick].type == "axis":
                    print(f"{fakeStick} -> {realStick}")
                    controller.inputs[fakeStick] = controller.inputs[realStick].replace(
                        name=fakeStick,
                        value=str(-int(controller.inputs[realStick].value))
                    )

        for inputIdx in controller.inputs:
                input = controller.inputs[inputIdx]
                if input.name in mupeninputs and mupeninputs[input.name] != "":
                        value=setControllerLine(input, mupeninputs[input.name], controller.inputs)
                        # Handle multiple inputs for a single N64 Pad input
                        if value != "":
                            if mupeninputs[input.name] not in config :
                                config[mupeninputs[input.name]] = value
                            else:
                                config[mupeninputs[input.name]] += f" {value}"
        return config

def setControllerLine(input: Input, mupenSettingName: str, allinputs: InputMapping) -> str:
        value = ''
        inputType = input.type
        if inputType == 'button':
            if mupenSettingName in ["X Axis", "Y Axis"]: # special case for these 2 axis...
                # hum, a button is mapped on an axis, find the reverse button
                if input.name == "up":
                    if "down" in allinputs:
                        reverseInput = allinputs["down"]
                        value = f"button({input.id}, {reverseInput.id})"
                    else:
                        value = f"button({input.id})"
                elif input.name == "left":
                    if "right" in allinputs:
                        reverseInput = allinputs["right"]
                        value = f"button({input.id}, {reverseInput.id})"
                    else:
                        value = f"button({input.id})"
                else:
                    return "" # skip down and right
            else:
                # normal button
                value = f"button({input.id})"
        elif inputType == 'hat':
                if mupenSettingName in ["X Axis", "Y Axis"]: # special case for these 2 axis...
                    if input.value == "1" or input.value == "8": # only for the lower value to avoid duplicate
                        value = f"hat({input.id} {mupenHatToAxis[input.value]} {mupenHatToReverseAxis[input.value]})"
                else:
                    value = f"hat({input.id} {mupenHatToAxis[input.value]})"
        elif inputType == 'axis':
                # Generic case for joystick1up and joystick1left
                if mupenSettingName in mupenDoubleAxis.values():
                        # X axis : value = -1 for left, +1 for right
                        # Y axis : value = -1 for up, +1 for down
                        # we configure only left and down to not configure 2 times each axis
                        if input.name in [ "left", "up", "joystick1left", "joystick1up", "joystick2left", "joystick2up" ]:
                            if input.value == "-1":
                                value = f"axis({input.id}-,{input.id}+)"
                            else:
                                value = f"axis({input.id}+,{input.id}-)"
                else:
                        if input.value == "1":
                                value = f"axis({input.id}+)"
                        else:
                                value = f"axis({input.id}-)"
        return value

def fillIniPlayer(nplayer: int, iniConfig: CaseSensitiveConfigParser, controller: Controller, config: dict[str, str]) -> None:
        section = f"Input-SDL-Control{nplayer}"

        # set static config
        if not iniConfig.has_section(section):
            iniConfig.add_section(section)
        iniConfig.set(section, 'Version', '2')
        iniConfig.set(section, 'mode', '0')
        iniConfig.set(section, 'device', str(controller.index))
        # TODO: python 3 remove hack to overcome ConfigParser limitation with utf8 in python 2.7
        name_encode = controller.real_name.encode("ascii", "ignore")
        iniConfig.set(section, 'name', str(name_encode))
        iniConfig.set(section, 'plugged', "True")
        iniConfig.set(section, 'plugin', '2')
        iniConfig.set(section, 'AnalogDeadzone', str(config['AnalogDeadzone']))
        iniConfig.set(section, 'AnalogPeak', str(config['AnalogPeak']))
        iniConfig.set(section, 'mouse', "False")

        # set dynamic config - clear all keys then fill
        iniConfig.set(section, "Mempak switch", "")
        iniConfig.set(section, "Rumblepak switch", "")
        iniConfig.set(section, "C Button R", "")
        iniConfig.set(section, "A Button", "")
        iniConfig.set(section, "C Button U", "")
        iniConfig.set(section, "B Button", "")
        iniConfig.set(section, "Start", "")
        iniConfig.set(section, "L Trig", "")
        iniConfig.set(section, "R Trig", "")
        iniConfig.set(section, "Z Trig", "")
        iniConfig.set(section, "DPad U", "")
        iniConfig.set(section, "DPad D", "")
        iniConfig.set(section, "DPad R", "")
        iniConfig.set(section, "DPad L", "")
        iniConfig.set(section, "Y Axis", "")
        iniConfig.set(section, "Y Axis", "")
        iniConfig.set(section, "X Axis", "")
        iniConfig.set(section, "X Axis", "")
        iniConfig.set(section, "C Button U", "")
        iniConfig.set(section, "C Button D", "")
        iniConfig.set(section, "C Button L", "")
        iniConfig.set(section, "C Button R", "")
        for inputName in sorted(config):
                iniConfig.set(section, inputName, config[inputName])

def cleanPlayer(nplayer: int, iniConfig: CaseSensitiveConfigParser) -> None:
        section = f"Input-SDL-Control{nplayer}"

        # set static config
        if not iniConfig.has_section(section):
            iniConfig.add_section(section)
        iniConfig.set(section, 'Version', '2')
        iniConfig.set(section, 'plugged', "False")

