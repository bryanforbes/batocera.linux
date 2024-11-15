from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, NotRequired, TypedDict

from ... import Command
from ...batoceraPaths import CONFIGS, mkdir_if_not_exists
from ...controller import Controller, generate_sdl_game_controller_config
from ...utils import videoMode
from ..Generator import Generator

if TYPE_CHECKING:
    from ...types import HotkeysContext


bigPemuConfig = CONFIGS / "bigpemu" / "BigPEmuConfig.bigpcfg"


class _ButtonControllerSequence(TypedDict):
    button: str
    keyboard: NotRequired[str]

class _ButtonComboControllerSequence(TypedDict):
    buttons: list[str]
    keyboard: NotRequired[str]

class _KeyboardControllerSequence(TypedDict):
    keyboard: str

class _BlankControllerSequence(TypedDict):
    blank: None


type _ControllerSequence = _ButtonControllerSequence | _ButtonComboControllerSequence | _KeyboardControllerSequence | _BlankControllerSequence

# BigPEmu controller sequence, P1 only requires keyboard inputs
# default standard bindings
P1_BINDINGS_SEQUENCE: dict[str, _ControllerSequence] = {
    "C": {"button": "y", "keyboard": "4"},
    "B": {"button": "b", "keyboard": "22"},
    "A": {"button": "a", "keyboard": "7"},
    "Pause": {"button": "select", "keyboard": "20"},
    "Option": {"button": "start", "keyboard": "26"},
    "Pad-Up": {"button": "up", "keyboard": "82"},
    "Pad-Down": {"button": "down", "keyboard": "81"},
    "Pad-Left": {"button": "left", "keyboard": "80"},
    "Pad-Right": {"button": "right", "keyboard": "79"},
    "Numpad-0": {"buttons": ["r3", "l2"], "keyboard": "39"},
    "Numpad-1": {"buttons": ["y", "l2"], "keyboard": "30"},
    "Numpad-2": {"buttons": ["x", "l2"], "keyboard": "31"},
    "Numpad-3": {"buttons": ["a", "l2"], "keyboard": "32"},
    "Numpad-4": {"button": "pageup", "keyboard": "33"},
    "Numpad-5": {"button": "x", "keyboard": "34"},
    "Numpad-6": {"button": "pagedown", "keyboard": "35"},
    "Numpad-7": {"buttons": ["pageup", "l2"], "keyboard": "36"},
    "Numpad-8": {"buttons": ["b", "l2"], "keyboard": "37"},
    "Numpad-9": {"buttons": ["pagedown", "l2"], "keyboard": "38"},
    "Asterick": {"button": "l3", "keyboard": "18"},
    "Pound": {"button": "r3", "keyboard": "19"},
    "Analog-0-left": {"button": "joystick1left"},
    #"Analog-0-right": {"button": "joystick1right"},
    "Analog-0-up": {"button": "joystick1up"},
    #"Analog-0-down": {"button": "joystick1down"},
    "Analog-1-left": {"button": "joystick2left"},
    #"Analog-1-right": {"button": "joystick2right"},
    "Analog-1-up": {"button": "joystick2up"},
    #"Analog-1-down": {"button": "joystick2down"},
    "Extra-Up": {"blank": None},
    "Extra-Down": {"blank": None},
    "Extra-Left": {"blank": None},
    "Extra-Right": {"blank": None},
    "Extra-A": {"blank": None},
    "Extra-B": {"blank": None},
    "Extra-C": {"blank": None},
    "Extra-D": {"blank": None},
    "Menu": {"buttons": ["start", "r2"], "keyboard": "41"},
    "Fast Forward": {"buttons": ["x", "r2"], "keyboard": "59"},
    "Rewind": {"blank": None},
    "Save State": {"keyboard": "66"},
    "Load State": {"keyboard": "62"},
    "Screenshot": {"keyboard": "63"},
    "Overlay": {"buttons": ["l3", "r2"]},
    "Chat": {"keyboard": "23"},
    "Blank1": {"blank": None},
    "Blank2": {"blank": None},
    "Blank3": {"blank": None},
    "Blank4": {"blank": None},
    "Blank5": {"blank": None}
}

# BigPEmu controller sequence, P2+
# default standard bindings
P2_BINDINGS_SEQUENCE: dict[str, _ControllerSequence] = {
    "C": {"button": "y"},
    "B": {"button": "b"},
    "A": {"button": "a"},
    "Pause": {"button": "select"},
    "Option": {"button": "start"},
    "Pad-Up": {"button": "up"},
    "Pad-Down": {"button": "down"},
    "Pad-Left": {"button": "left"},
    "Pad-Right": {"button": "right"},
    "Numpad-0": {"buttons": ["r3", "l2"]},
    "Numpad-1": {"buttons": ["y", "l2"]},
    "Numpad-2": {"buttons": ["x", "l2"]},
    "Numpad-3": {"buttons": ["a", "l2"]},
    "Numpad-4": {"button": "pageup"},
    "Numpad-5": {"button": "x"},
    "Numpad-6": {"button": "pagedown"},
    "Numpad-7": {"buttons": ["pageup", "l2"]},
    "Numpad-8": {"buttons": ["b", "l2"]},
    "Numpad-9": {"buttons": ["pagedown", "l2"]},
    "Asterick": {"button": "l3"},
    "Pound": {"button": "r3"},
    "Analog-0-left": {"button": "joystick1left"},
    #"Analog-0-right": {"button": "joystick1right"},
    "Analog-0-up": {"button": "joystick1up"},
    #"Analog-0-down": {"button": "joystick1down"},
    "Analog-1-left": {"button": "joystick2left"},
    #"Analog-1-right": {"button": "joystick2right"},
    "Analog-1-up": {"button": "joystick2up"},
    #"Analog-1-down": {"button": "joystick2down"},
    "Extra-Up": {"blank": None},
    "Extra-Down": {"blank": None},
    "Extra-Left": {"blank": None},
    "Extra-Right": {"blank": None},
    "Extra-A": {"blank": None},
    "Extra-B": {"blank": None},
    "Extra-C": {"blank": None},
    "Extra-D": {"blank": None}
}

type _Trigger = dict[str, bool | float | str]
type _Bindings = list[dict[str, list[_Trigger]]]

def _generate_bindings(pad: Controller, binding_info: _ButtonControllerSequence | _ButtonComboControllerSequence, /) -> _Bindings:
    bindings: _Bindings = []

    for input in pad.inputs.values():
        # workaround values for SDL2
        input_value = '0' if input.type == 'button' else input.value
        input_id = input.id

        if input.type == 'hat':
            input_id = '134'

        if input.name == 'joystick1left':
            input_id = '128'
        elif input.name == 'joystick1up':
            input_id = '129'
        elif input.name == 'joystick2left':
            input_id = '131'
        elif input.name == 'joystick2up':
            input_id = '132'

        if 'button' in binding_info and input.name == binding_info['button']:
            if 'keyboard' in binding_info:
                bindings += _generate_keyb_button_bindings(pad.guid, binding_info['keyboard'], input_id, input_value)
            else:
                bindings += _generate_button_bindings(pad.guid, input_id, input_value)

            if input.name.startswith('joystick1') or input.name.startswith('joystick2'):
                # For joysticks, generate two bindings with positive and then negative values
                if "keyboard" in binding_info:
                    bindings += _generate_keyb_button_bindings(pad.guid, binding_info['keyboard'], input_id, -float(input_value))
                else:
                    bindings += _generate_button_bindings(pad.guid, input_id, -float(input_value))

        elif 'buttons' in binding_info and input.name in binding_info['buttons']:
            # Handle combo bindings
            button_bindings: list[str] = []

            for button_name in binding_info['buttons']:
                if (button_input := pad.inputs.get(button_name)) is not None:
                    # workaround values for SDL2 here as well
                    button_input_value = '0' if button_input.type == 'button' else button_input.value
                    button_input_id = button_input.id

                    if button_input.name == "l2":
                        button_input_id = "130"
                    elif button_input.name == "r2":
                        button_input_id = "133"

                    button_bindings += [button_input_id, button_input_value]

            if len(button_bindings) >= 4:
                device_id = pad.guid.upper()

                if 'keyboard' in binding_info:
                    bindings.append({
                        "Triggers": [
                            {
                                "B_KB": True,
                                "B_ID": int(binding_info['keyboard']),
                                "B_AH": 0.0
                            },
                            {
                                "B_KB": False,
                                "B_ID": int(button_bindings[0]),
                                "B_AH": float(button_bindings[1]),
                                "B_DevID": device_id,
                                "M_KB": False,
                                "M_ID": int(button_bindings[2]),
                                "M_AH": float(button_bindings[3]),
                                "M_DevID": device_id
                            }
                        ]
                    })
                else:
                    bindings.append({
                        "Triggers": [
                            {
                                "B_KB": False,
                                "B_ID": int(button_bindings[0]),
                                "B_AH": float(button_bindings[1]),
                                "B_DevID": device_id,
                                "M_KB": False,
                                "M_ID": int(button_bindings[2]),
                                "M_AH": float(button_bindings[3]),
                                "M_DevID": device_id
                            }
                        ]
                    })

    return bindings

def _generate_keyb_button_bindings(device_id: str, keyb_id: str, button_id: str, button_value: str | float) -> _Bindings:
    return [
        {
            "Triggers": [
                {
                    "B_KB": True,
                    "B_ID": int(keyb_id),
                    "B_AH": 0.0
                },
                {
                    "B_KB": False,
                    "B_ID": int(button_id),
                    "B_AH": float(button_value),
                    "B_DevID": device_id.upper()
                }
            ]
        }
    ]

def _generate_button_bindings(device_id: str, button_id: str, button_value: str | float) -> _Bindings:
    return [
        {
            "Triggers": [
                {
                    "B_KB": False,
                    "B_ID": int(button_id),
                    "B_AH": float(button_value),
                    "B_DevID": device_id.upper()
                }
            ]
        }
    ]

class BigPEmuGenerator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "bigpemu",
            "keys": { "exit": ["KEY_LEFTALT", "KEY_F4"], "menu": "KEY_ESC", "save_state": "KEY_F9", "restore_state": "KEY_F5" }
        }

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):

        mkdir_if_not_exists(bigPemuConfig.parent)

        # Delete the config file to update controllers
        # As it doesn't like to be updated
        # ¯\_(ツ)_/¯
        if bigPemuConfig.exists():
            bigPemuConfig.unlink()

        config: dict[str, Any] = {}

        # Ensure the necessary structure in the config
        config["BigPEmuConfig"] = {}
        config["BigPEmuConfig"]["Video"] = {}

        # Adjust basic settings
        config["BigPEmuConfig"]["Video"]["DisplayMode"] = 2
        config["BigPEmuConfig"]["Video"]["ScreenScaling"] = 5
        config["BigPEmuConfig"]["Video"]["DisplayWidth"] = gameResolution["width"]
        config["BigPEmuConfig"]["Video"]["DisplayHeight"] = gameResolution["height"]
        config["BigPEmuConfig"]["Video"]["DisplayFrequency"] = int(round(float(videoMode.getRefreshRate())))

        # User selections
        config["BigPEmuConfig"]["Video"]["VSync"] = system.get_option("bigpemu_vsync", 1)
        config["BigPEmuConfig"]["Video"]["ScreenAspect"] = system.get_option_int("bigpemu_ratio", 2)
        config["BigPEmuConfig"]["Video"]["LockAspect"] = 1

        # Controller config
        config["BigPEmuConfig"]["Input"] = {}

        # initial settings
        config["BigPEmuConfig"]["Input"]["DeviceCount"] = len(playersControllers)
        config["BigPEmuConfig"]["Input"]["AnalDeadMice"] = 0.25
        config["BigPEmuConfig"]["Input"]["AnalToDigi"] = 0.25
        config["BigPEmuConfig"]["Input"]["AnalExpo"] = 0.0
        config["BigPEmuConfig"]["Input"]["ConflictingPad"] = 0
        config["BigPEmuConfig"]["Input"]["XboxAnus"] = 0
        config["BigPEmuConfig"]["Input"]["OLAnchor"] = 3
        config["BigPEmuConfig"]["Input"]["OLScale"] = 0.75
        config["BigPEmuConfig"]["Input"]["MouseInput"] = 0
        config["BigPEmuConfig"]["Input"]["MouseSens"] = 1.0
        config["BigPEmuConfig"]["Input"]["MouseThresh"] = 0.5

        # per controller settings (standard controller only currently)
        for nplayer, pad in enumerate(sorted(playersControllers.values())):
            if nplayer <= 7 and (player_key := f"Device{nplayer}") not in config["BigPEmuConfig"]["Input"]:
                player_input_config: dict[str, Any] = {}
                player_input_bindings: _Bindings = []
                config["BigPEmuConfig"]["Input"][player_key] = player_input_config

                player_input_config["DeviceType"] = 0 # standard controller
                player_input_config["InvertAnally"] = 0
                player_input_config["RotaryScale"] = 0.5
                player_input_config["HeadTrackerScale"] = 8.0
                player_input_config["HeadTrackerSpring"] = 0
                player_input_config["Bindings"] = player_input_bindings

                # Loop through BINDINGS_SEQUENCE to maintain the specific order of bindings
                BINDINGS_SEQUENCE = P1_BINDINGS_SEQUENCE if nplayer == 0 else P2_BINDINGS_SEQUENCE

                for binding_info in BINDINGS_SEQUENCE.values():
                    # _logger.debug(f"Binding sequence input: %s", binding_key)
                    if "blank" in binding_info:
                        player_input_bindings.append({
                            "Triggers": []
                        })
                    elif "keyboard" in binding_info and "button" not in binding_info and "buttons" not in binding_info:
                        player_input_bindings.append({
                            "Triggers": [
                                {
                                    "B_KB": True,
                                    "B_ID": int(binding_info["keyboard"]),
                                    "B_AH": 0.0
                                }
                            ]
                        })
                    else:
                        player_input_bindings += _generate_bindings(pad, binding_info)

        # Scripts config
        config["BigPEmuConfig"]["ScriptsEnabled"] = []

        # User selections for ScriptsEnabled options (individual scripts)
        scripts = [
            ("avp", "bigpemu_avp"),
            ("avp_mp", "bigpemu_avp_mp"),
            ("brett_hull_hockey", "bigpemu_brett_hull_hockey"),
            ("checkered_flag", "bigpemu_checkered_flag"),
            ("cybermorph", "bigpemu_cybermorph"),
            ("doom", "bigpemu_doom"),
            ("iron_soldier", "bigpemu_iron_soldier"),
            ("mc3d_vr", "bigpemu_mc3d_vr"),
            ("t2k_rotary", "bigpemu_t2k_rotary"),
            ("wolf3d", "bigpemu_wolf3d")
        ]

        config["BigPEmuConfig"]["ScriptsEnabled"] += [
            script_name for script_name, script_option in scripts if system.get_option(script_option) == "1"
        ]

        # Remove duplicates just in case (as a precaution)
        config["BigPEmuConfig"]["ScriptsEnabled"] = list(set(config["BigPEmuConfig"]["ScriptsEnabled"]))

        # ScriptSettings
        config["BigPEmuConfig"]["ScriptSettings"] = {}

        config["BigPEmuConfig"]["ScriptSettings"]["DOOM-Music"] = system.get_option("bigpemu_doom", 0)

        # Screen filter
        config["BigPEmuConfig"]["Video"]["ScreenFilter"] = system.get_option("bigpemu_screenfilter", 0)

        # Close off input
        config["BigPEmuConfig"]["Input"]["InputVer"] = 2
        config["BigPEmuConfig"]["Input"]["InputPluginVer"] = 666

        with bigPemuConfig.open("w") as file:
            json.dump(config, file, indent=4)

        # Run the emulator
        commandArray = ["/usr/bigpemu/bigpemu", rom, "-cfgpathabs", str(bigPemuConfig)]

        environment = {
            "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers),
            "SDL_JOYSTICK_HIDAPI": "0"
        }

        return Command.Command(array=commandArray, env=environment)

    def getInGameRatio(self, config, gameResolution, rom):
        if "bigpemu_ratio" in config:
            if config['bigpemu_ratio'] == "8":
                return 16/9
            else:
                return 4/3
        else:
            return 4/3
