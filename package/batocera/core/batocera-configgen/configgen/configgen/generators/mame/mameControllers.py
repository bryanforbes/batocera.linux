from __future__ import annotations

import codecs
import csv
import logging
import os
from typing import TYPE_CHECKING, Final, Literal, TypeAlias, TypedDict, cast
from xml.dom import minidom

from .mamePaths import MAME_CONFIG, MAME_DEFAULT_DATA

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from ...controller import Controller, ControllerMapping
    from ...Emulator import Emulator
    from ...gun import GunMapping
    from ...input import Input
    from ...types import DeviceInfoMapping

_logger = logging.getLogger(__name__)


class _MessControlBase(TypedDict):
    player: int
    tag: str
    key: str
    reversed: bool

class _MessMainOrSpecialControl(_MessControlBase):
    type: Literal['special', 'main']
    mapping: str
    useMapping: str
    mask: str
    default: str

class _MessAnalogControl(_MessControlBase):
    type: Literal['analog']
    incMapping: str
    decMapping: str
    useMapping1: str
    useMapping2: str
    mask: str
    default: str
    delta: str
    axis: str

class _MessComboControl(_MessControlBase):
    type: Literal['combo']
    kbMapping: str
    mapping: str
    useMapping: str
    mask: str
    default: str


_MessControl: TypeAlias = _MessMainOrSpecialControl | _MessAnalogControl | _MessComboControl

_SPECIAL_SYSTEMS: Final = {
    "cdimono1", "apfm1000", "astrocde", "adam", "arcadia", "gamecom", "tutor", "crvision", "bbcb", "bbcm", "bbcm512", "bbcmc", "xegs",
    "socrates", "vgmplay", "pdp1", "vc4000", "fmtmarty", "gp32", "apple2p", "apple2e", "apple2ee"
}

def parse_mess_controls(system_name: str, /) -> dict[str, dict[str, _MessControl]]:
    mess_controls: dict[str, dict[str, _MessControl]] = {}

    if system_name in _SPECIAL_SYSTEMS:
        # Load mess controls from csv
        with (MAME_DEFAULT_DATA / 'messControls.csv').open() as mess_controls_csv:
            for row_system, row_control, row_type, row_player, row_tag, row_key, *row in csv.reader(mess_controls_csv, delimiter=';'):
                if row_system not in mess_controls:
                    mess_controls[row_system] = {}

                if row_type == 'special' or row_type == 'main':
                    mess_controls[row_system][row_control] = {
                        'type': cast(Literal['special', 'main'], row_type),
                        'player': int(row_player),
                        'tag': row_tag,
                        'key': row_key,
                        'mapping': row[0],
                        'useMapping': row[1],
                        'reversed': row[2] == 'False',
                        'mask': row[3],
                        'default': row[4],
                    }
                elif row_type == 'analog':
                    mess_controls[row_system][row_control] = {
                        'type': cast(Literal['analog'], row_type),
                        'player': int(row_player),
                        'tag': row_tag,
                        'key': row_key,
                        'incMapping': row[0],
                        'decMapping': row[1],
                        'useMapping1': row[2],
                        'useMapping2': row[3],
                        'reversed': row[4] == 'False',
                        'mask': row[5],
                        'default': row[6],
                        'delta': row[7],
                        'axis': row[8],
                    }
                else:
                    mess_controls[row_system][row_control] = {
                        'type': cast(Literal['combo'], row_type),
                        'player': int(row_player),
                        'tag': row_tag,
                        'key': row_key,
                        'kbMapping': row[0],
                        'mapping': row[1],
                        'useMapping': row[2],
                        'reversed': row[3] == 'False',
                        'mask': row[4],
                        'default': row[5],
                    }

    return mess_controls

def generatePadsConfig(cfgPath: Path, playersControllers: ControllerMapping, sysName: str, altButtons: str | int, customCfg: bool, specialController: str, decorations: str | None, useGuns: bool, guns: GunMapping, useWheels: bool, wheels: DeviceInfoMapping, useMouse: bool, multiMouse: bool, system: Emulator) -> None:
    # config file
    config = minidom.Document()
    configFile = cfgPath / "default.cfg"
    if configFile.exists():
        try:
            config = minidom.parse(str(configFile))
        except Exception:
            pass # reinit the file
    overwriteMAME = not (configFile.exists() and customCfg)

    # Load standard controls from csv
    controlFile = MAME_DEFAULT_DATA / 'mameControls.csv'
    controlDict: dict[str, dict[str, str]] = {}
    with controlFile.open('r') as openFile:
        controlList = csv.reader(openFile)
        for row in controlList:
            if row[0] not in controlDict:
                controlDict[row[0]] = {}
            controlDict[row[0]][row[1]] = row[2]

    # Common controls
    mappings: dict[str, str] = {}
    for controlDefKey, controlDefValue in controlDict['default'].items():
        mappings[controlDefKey] = controlDefValue

    # Only use gun buttons if lightguns are enabled to prevent conflicts with mouse
    gunmappings: dict[str, str] = {}
    if useGuns:
        for controlDefKey, controlDefValue in controlDict['gunbuttons'].items():
            gunmappings[controlDefKey] = controlDefValue

    # Only define mouse buttons if mouse is enabled, to prevent unwanted inputs
    # For a standard mouse, left, right, scroll wheel should be mapped to action buttons, and if side buttons are available, they will be coin & start
    mousemappings: dict[str, str] = {}
    if useMouse:
        for controlDefKey, controlDefValue in controlDict['mousebuttons'].items():
            mousemappings[controlDefKey] = controlDefValue

    # Buttons that change based on game/setting
    if altButtons in controlDict:
        for controlDefKey, controlDefValue in controlDict[altButtons].items():
            mappings.update({controlDefKey: controlDefValue})

    xml_mameconfig = getRoot(config, "mameconfig")
    xml_mameconfig.setAttribute("version", "10") # otherwise, config of pad won't work at first run (batocera v33)
    xml_system     = getSection(config, xml_mameconfig, "system")
    xml_system.setAttribute("name", "default")

    # crosshairs
    removeSection(config, xml_system, "crosshairs")
    xml_crosshairs = config.createElement("crosshairs")
    for p in range(0, 4):
        xml_crosshair = config.createElement("crosshair")
        xml_crosshair.setAttribute("player", str(p))
        if (mame_crosshair := system.get_option("mame_crosshair")) == "enabled":
            xml_crosshair.setAttribute("mode", "1")
        elif mame_crosshair == "onmove":
            continue # keep no line
        else:
            xml_crosshair.setAttribute("mode", "0")
        xml_crosshairs.appendChild(xml_crosshair)
    xml_system.appendChild(xml_crosshairs)

    removeSection(config, xml_system, "input")
    xml_input = config.createElement("input")
    xml_system.appendChild(xml_input)

    if sysName in [ "bbcb", "bbcm", "bbcm512", "bbcmc" ]:
        useControls = "bbc" if specialController == "none" else f"bbc-{specialController}"
    elif sysName in [ "apple2p", "apple2e", "apple2ee" ]:
        useControls = "apple2" if specialController == "none" else f"apple2-{specialController}"
    else:
        useControls = sysName
    _logger.debug("Using %s for controller config.", useControls)

    # Open or create alternate config file for systems with special controllers/settings
    # If the system/game is set to per game config, don't try to open/reset an existing file, only write if it's blank or going to the shared cfg folder
    messControlDict = parse_mess_controls(sysName)

    if messControlDict:
        config_alt = minidom.Document()
        configFile_alt = cfgPath / f"{sysName}.cfg"
        if configFile_alt.exists() and cfgPath == (MAME_CONFIG / sysName):
            try:
                config_alt = minidom.parse(str(configFile_alt))
            except Exception:
                pass # reinit the file
        elif configFile_alt.exists():
            try:
                config_alt = minidom.parse(str(configFile_alt))
            except Exception:
                pass # reinit the file
        perGameCfg = cfgPath != MAME_CONFIG / sysName
        overwriteSystem = not (configFile_alt.exists() and (customCfg or perGameCfg))

        xml_mameconfig_alt = getRoot(config_alt, "mameconfig")
        xml_mameconfig_alt.setAttribute("version", "10")
        xml_system_alt = getSection(config_alt, xml_mameconfig_alt, "system")
        xml_system_alt.setAttribute("name", sysName)

        removeSection(config_alt, xml_system_alt, "input")
        xml_input_alt = config_alt.createElement("input")
        xml_system_alt.appendChild(xml_input_alt)

        # Hide the LCD display on CD-i
        if useControls == "cdimono1":
            removeSection(config_alt, xml_system_alt, "video")
            xml_video_alt = config_alt.createElement("video")
            xml_system_alt.appendChild(xml_video_alt)

            xml_screencfg_alt = config_alt.createElement("target")
            xml_screencfg_alt.setAttribute("index", "0")
            if decorations == "none":
                xml_screencfg_alt.setAttribute("view", "Main Screen Standard (4:3)")
            else:
                xml_screencfg_alt.setAttribute("view", "Upright_Artwork")
            xml_video_alt.appendChild(xml_screencfg_alt)

        # If using BBC keyboard controls, enable keyboard to gamepad
        if useControls == 'bbc':
            xml_kbenable_alt = config_alt.createElement("keyboard")
            xml_kbenable_alt.setAttribute("tag", ":")
            xml_kbenable_alt.setAttribute("enabled", "1")
            xml_input_alt.appendChild(xml_kbenable_alt)

    # Fill in controls on cfg files
    maxplayers = len(playersControllers)
    for nplayer, pad in enumerate(sorted(playersControllers.values()), start=1):
        mappings_use = mappings.copy()
        if not hasStick(pad):
            mappings_use["JOYSTICK_UP"] = "up"
            mappings_use["JOYSTICK_DOWN"] = "down"
            mappings_use["JOYSTICK_LEFT"] = "left"
            mappings_use["JOYSTICK_RIGHT"] = "right"

        # wheel mappings
        isWheel = False
        if useWheels:
            for w in wheels.values():
                if w["joystick_index"] == pad.index:
                    isWheel = True
                    _logger.debug("player %s has a wheel", nplayer)
            if isWheel:
                mappings_use = {key: value for key, value in mappings_use.items() if value != "l2" and value != "r2" and value != "joystick1lef"}
                mappings_use["PEDAL"] = "r2"
                mappings_use["PEDAL2"] = "l2"
                mappings_use["PADDLE"] = "joystick1left"

        addCommonPlayerPorts(config, xml_input, nplayer)

        ### find a keyboard key to simulate the action of the player (always like button 2) ; search in batocera.conf, else default config
        pedalsKeys = {1: "c", 2: "v", 3: "b", 4: "n"}
        pedalkey: str | None = None
        pedalcname = f"controllers.pedals{nplayer}"
        if (config_pedalkey := system.get_option_str(pedalcname)) is not system.MISSING:
            pedalkey = config_pedalkey
        else:
            if nplayer in pedalsKeys:
                pedalkey = pedalsKeys[nplayer]
        ###

        for mapping, mapping_key in mappings_use.items():
            if mapping_key in pad.inputs:
                if mapping in [ 'START', 'COIN' ]:
                    xml_input.appendChild(generateSpecialPortElementPlayer(pad, config, 'standard', nplayer, pad.index, mapping, mapping_key, pad.inputs[mapping_key], False, "", "", gunmappings, mousemappings, multiMouse, pedalkey))
                else:
                    xml_input.appendChild(generatePortElement(pad, config, nplayer, pad.index, mapping, mapping_key, pad.inputs[mapping_key], False, altButtons, gunmappings, isWheel, mousemappings, multiMouse, pedalkey))
            else:
                rmapping = reverseMapping(mapping_key)
                if rmapping in pad.inputs:
                        xml_input.appendChild(generatePortElement(pad, config, nplayer, pad.index, mapping, mapping_key, pad.inputs[rmapping], True, altButtons, gunmappings, isWheel, mousemappings, multiMouse, pedalkey))

        #UI Mappings
        if nplayer == 1:
            xml_input.appendChild(generateComboPortElement(pad, config, 'standard', pad.index, "UI_DOWN", "DOWN", mappings_use["JOYSTICK_DOWN"], pad.inputs[mappings_use["JOYSTICK_UP"]], False, "", ""))      # Down
            xml_input.appendChild(generateComboPortElement(pad, config, 'standard', pad.index, "UI_LEFT", "LEFT", mappings_use["JOYSTICK_LEFT"], pad.inputs[mappings_use["JOYSTICK_LEFT"]], False, "", ""))    # Left
            xml_input.appendChild(generateComboPortElement(pad, config, 'standard', pad.index, "UI_UP", "UP", mappings_use["JOYSTICK_UP"], pad.inputs[mappings_use["JOYSTICK_UP"]], False, "", ""))            # Up
            xml_input.appendChild(generateComboPortElement(pad, config, 'standard', pad.index, "UI_RIGHT", "RIGHT", mappings_use["JOYSTICK_RIGHT"], pad.inputs[mappings_use["JOYSTICK_LEFT"]], False, "", "")) # Right
            xml_input.appendChild(generateComboPortElement(pad, config, 'standard', pad.index, "UI_SELECT", "ENTER", 'b', pad.inputs['b'], False, "", ""))                                                     # Select

        if useControls in messControlDict:
            for thisControl in messControlDict[useControls].values():
                if nplayer == thisControl['player']:
                    if thisControl['type'] == 'special':
                        xml_input_alt.appendChild(generateSpecialPortElement(pad, config_alt, thisControl['tag'], nplayer, pad.index, thisControl['key'], thisControl['mapping'], \
                            pad.inputs[mappings_use[thisControl['useMapping']]], thisControl['reversed'], thisControl['mask'], thisControl['default'], pedalkey))
                    elif thisControl['type'] == 'main':
                        xml_input.appendChild(generateSpecialPortElement(pad, config_alt, thisControl['tag'], nplayer, pad.index, thisControl['key'], thisControl['mapping'], \
                            pad.inputs[mappings_use[thisControl['useMapping']]], thisControl['reversed'], thisControl['mask'], thisControl['default'], pedalkey))
                    elif thisControl['type'] == 'analog':
                        xml_input_alt.appendChild(generateAnalogPortElement(pad, config_alt, thisControl['tag'], nplayer, pad.index, thisControl['key'], mappings_use[thisControl['incMapping']], \
                            mappings_use[thisControl['decMapping']], pad.inputs[mappings_use[thisControl['useMapping1']]], pad.inputs[mappings_use[thisControl['useMapping2']]], thisControl['reversed'], \
                            thisControl['mask'], thisControl['default'], thisControl['delta'], thisControl['axis']))
                    elif thisControl['type'] == 'combo':
                        xml_input_alt.appendChild(generateComboPortElement(pad, config_alt, thisControl['tag'], pad.index, thisControl['key'], thisControl['kbMapping'], thisControl['mapping'], \
                            pad.inputs[mappings_use[thisControl['useMapping']]], thisControl['reversed'], thisControl['mask'], thisControl['default']))

    # in case there are more guns than pads, configure them
    if useGuns and len(guns) > len(playersControllers):
        for gunnum in range(len(playersControllers)+1, len(guns)+1):
            ### find a keyboard key to simulate the action of the player (always like button 2) ; search in batocera.conf, else default config
            pedalsKeys = {1: "c", 2: "v", 3: "b", 4: "n"}
            pedalkey = None
            pedalcname = f"controllers.pedals{gunnum}"
            if (config_pedalkey := system.get_option_str(pedalcname)) is not system.MISSING:
                pedalkey = config_pedalkey
            else:
                if gunnum in pedalsKeys:
                    pedalkey = pedalsKeys[gunnum]
            ###
            addCommonPlayerPorts(config, xml_input, gunnum)
            for mapping in gunmappings:
                xml_input.appendChild(generateGunPortElement(config, gunnum, mapping, gunmappings, pedalkey))

    # save the config file
    #mameXml = open(configFile, "w")
    # TODO: python 3 - workawround to encode files in utf-8
    if overwriteMAME:
        _logger.debug("Saving %s", configFile)
        with codecs.open(str(configFile), "w", "utf-8") as mameXml:
            dom_string = os.linesep.join([s for s in config.toprettyxml().splitlines() if s.strip()]) # remove ugly empty lines while minicom adds them...
            mameXml.write(dom_string)

    # Write alt config (if used, custom config is turned off or file doesn't exist yet)
    if messControlDict and overwriteSystem:
        _logger.debug("Saving %s", configFile_alt)
        with codecs.open(str(configFile_alt), "w", "utf-8") as mameXml_alt:
            dom_string_alt = os.linesep.join([s for s in config_alt.toprettyxml().splitlines() if s.strip()]) # remove ugly empty lines while minicom adds them...
            mameXml_alt.write(dom_string_alt)

def reverseMapping(key: str) -> str | None:
    if key == "joystick1down":
        return "joystick1up"
    if key == "joystick1right":
        return "joystick1left"
    if key == "joystick2down":
        return "joystick2up"
    if key == "joystick2right":
        return "joystick2left"
    return None

def generatePortElement(pad: Controller, config: minidom.Document, nplayer: int, padindex: int, mapping: str, key: str, input: Input, reversed: bool, altButtons: str | int, gunmappings: Mapping[str, str], isWheel: bool, mousemappings: Mapping[str, str], multiMouse: bool, pedalkey: str | None):
    # Generic input
    xml_port = config.createElement("port")
    xml_port.setAttribute("type", f"P{nplayer}_{mapping}")
    xml_newseq = config.createElement("newseq")
    xml_newseq.setAttribute("type", "standard")
    xml_port.appendChild(xml_newseq)
    keyval = input2definition(pad, key, input, padindex + 1, reversed, altButtons, False, isWheel)
    if mapping in gunmappings:
        keyval = keyval + f" OR GUNCODE_{nplayer}_{gunmappings[mapping]}"
        if gunmappings[mapping] == "BUTTON2" and pedalkey is not None:
            keyval += " OR KEYCODE_" + pedalkey.upper()
    if mapping in mousemappings:
        if multiMouse:
            keyval = keyval + f" OR MOUSECODE_{nplayer}_{mousemappings[mapping]}"
        else:
            keyval = keyval + f" OR MOUSECODE_1_{mousemappings[mapping]}"
    value = config.createTextNode(keyval)
    xml_newseq.appendChild(value)
    return xml_port

def generateGunPortElement(config: minidom.Document, nplayer: int, mapping: str, gunmappings: Mapping[str, str], pedalkey: str | None):
    # Generic input
    xml_port = config.createElement("port")
    if mapping in ["START", "COIN"]:
        xml_port.setAttribute("type", mapping+str(nplayer))
    else:
        xml_port.setAttribute("type", f"P{nplayer}_{mapping}")
    xml_newseq = config.createElement("newseq")
    xml_newseq.setAttribute("type", "standard")
    xml_port.appendChild(xml_newseq)
    keyval = None
    if mapping in gunmappings:
        keyval = f"GUNCODE_{nplayer}_{gunmappings[mapping]}"
        if gunmappings[mapping] == "BUTTON2" and pedalkey is not None:
            keyval += " OR KEYCODE_" + pedalkey.upper()
    if keyval is None:
        return None
    value = config.createTextNode(keyval)
    xml_newseq.appendChild(value)
    return xml_port

def generateSpecialPortElementPlayer(pad: Controller, config: minidom.Document, tag: str, nplayer: int, padindex: int, mapping: str, key: str, input: Input, reversed: bool, mask: str, default: str, gunmappings: Mapping[str, str], mousemappings: Mapping[str, str], multiMouse: bool, pedalkey: str | None):
    # Special button input (ie mouse button to gamepad)
    xml_port = config.createElement("port")
    xml_port.setAttribute("tag", tag)
    xml_port.setAttribute("type", mapping+str(nplayer))
    xml_port.setAttribute("mask", mask)
    xml_port.setAttribute("defvalue", default)
    xml_newseq = config.createElement("newseq")
    xml_newseq.setAttribute("type", "standard")
    xml_port.appendChild(xml_newseq)
    keyval = input2definition(pad, key, input, padindex + 1, reversed, 0)
    if mapping == "COIN" and nplayer <= 4:
        keyval = keyval + f" OR KEYCODE_{nplayer}_{nplayer + 4!s}" # 5 for player 1, 6 for player 2, 7 for player 3 and 8 for player 4
    if mapping in gunmappings:
        keyval = keyval + f" OR GUNCODE_{nplayer}_{gunmappings[mapping]}"
        if gunmappings[mapping] == "BUTTON2" and pedalkey is not None:
            keyval += " OR KEYCODE_" + pedalkey.upper()
    if mapping in mousemappings:
        if multiMouse:
            keyval = keyval + f" OR MOUSECODE_{nplayer}_{mousemappings[mapping]}"
        else:
            keyval = keyval + f" OR MOUSECODE_1_{mousemappings[mapping]}"
    value = config.createTextNode(keyval)
    xml_newseq.appendChild(value)
    return xml_port

def generateSpecialPortElement(pad: Controller, config: minidom.Document, tag: str, nplayer: int, padindex: int, mapping: str, key: str, input: Input, reversed: bool, mask: str, default: str, pedalkey: str | None):
    # Special button input (ie mouse button to gamepad)
    xml_port = config.createElement("port")
    xml_port.setAttribute("tag", tag)
    xml_port.setAttribute("type", mapping)
    xml_port.setAttribute("mask", mask)
    xml_port.setAttribute("defvalue", default)
    xml_newseq = config.createElement("newseq")
    xml_newseq.setAttribute("type", "standard")
    xml_port.appendChild(xml_newseq)
    value = config.createTextNode(input2definition(pad, key, input, padindex + 1, reversed, 0))
    xml_newseq.appendChild(value)
    return xml_port

def generateComboPortElement(pad: Controller, config: minidom.Document, tag: str, padindex: int, mapping: str, kbkey: str, key: str, input: Input, reversed: bool, mask: str, default: str):
    # Maps a keycode + button - for important keyboard keys when available
    xml_port = config.createElement("port")
    xml_port.setAttribute("tag", tag)
    xml_port.setAttribute("type", mapping)
    xml_port.setAttribute("mask", mask)
    xml_port.setAttribute("defvalue", default)
    xml_newseq = config.createElement("newseq")
    xml_newseq.setAttribute("type", "standard")
    xml_port.appendChild(xml_newseq)
    value = config.createTextNode(f"KEYCODE_{kbkey} OR " + input2definition(pad, key, input, padindex + 1, reversed, 0))
    xml_newseq.appendChild(value)
    return xml_port

def generateAnalogPortElement(pad: Controller, config: minidom.Document, tag: str, nplayer: int, padindex: int, mapping: str, inckey: str, deckey: str, mappedinput: Input, mappedinput2: Input, reversed: bool, mask: str, default: str, delta: str, axis: str = ''):
    # Mapping analog to digital (mouse, etc)
    xml_port = config.createElement("port")
    xml_port.setAttribute("tag", tag)
    xml_port.setAttribute("type", mapping)
    xml_port.setAttribute("mask", mask)
    xml_port.setAttribute("defvalue", default)
    xml_port.setAttribute("keydelta", delta)
    xml_newseq_inc = config.createElement("newseq")
    xml_newseq_inc.setAttribute("type", "increment")
    xml_port.appendChild(xml_newseq_inc)
    incvalue = config.createTextNode(input2definition(pad, inckey, mappedinput, padindex + 1, reversed, 0, True))
    xml_newseq_inc.appendChild(incvalue)
    xml_newseq_dec = config.createElement("newseq")
    xml_port.appendChild(xml_newseq_dec)
    xml_newseq_dec.setAttribute("type", "decrement")
    decvalue = config.createTextNode(input2definition(pad, deckey, mappedinput2, padindex + 1, reversed, 0, True))
    xml_newseq_dec.appendChild(decvalue)
    xml_newseq_std = config.createElement("newseq")
    xml_port.appendChild(xml_newseq_std)
    xml_newseq_std.setAttribute("type", "standard")
    stdvalue = config.createTextNode("NONE" if not axis else f"JOYCODE_{padindex + 1}_{axis}")
    xml_newseq_std.appendChild(stdvalue)
    return xml_port

def input2definition(pad: Controller, key: str, input: Input, joycode: int, reversed: bool, altButtons: str | int, ignoreAxis: bool = False, isWheel: bool = False):

    mameAxisMappingNames = {0: "XAXIS", 1: "YAXIS", 2: "ZAXIS", 3: "RXAXIS", 4: "RYAXIS", 5: "RZAXIS"}

    if isWheel:
        if key == "joystick1left" or key == "l2" or key == "r2":
            suffix = ""
            if key == "r2":
                suffix = "_NEG"
            if key == "l2":
                suffix = "_NEG"
            if int(input.id) in mameAxisMappingNames:
                idname = mameAxisMappingNames[int(input.id)]
                return f"JOYCODE_{joycode}_{idname}{suffix}"

    if input.type == "button":
        return f"JOYCODE_{joycode}_BUTTON{int(input.id)+1}"
    elif input.type == "hat":
        if input.value == "1":
            return f"JOYCODE_{joycode}_HAT1UP"
        elif input.value == "2":
            return f"JOYCODE_{joycode}_HAT1RIGHT"
        elif input.value == "4":
            return f"JOYCODE_{joycode}_HAT1DOWN"
        elif input.value == "8":
            return f"JOYCODE_{joycode}_HAT1LEFT"
    elif input.type == "axis":
        # Determine alternate button for D-Pad and right stick as buttons
        dpadInputs: dict[str, str] = {}
        for direction in ['up', 'down', 'left', 'right']:
            if pad.inputs[direction].type == 'button':
                dpadInputs[direction] = f'JOYCODE_{joycode}_BUTTON{int(pad.inputs[direction].id)+1}'
            elif pad.inputs[direction].type == 'hat':
                if pad.inputs[direction].value == "1":
                    dpadInputs[direction] = f'JOYCODE_{joycode}_HAT1UP'
                if pad.inputs[direction].value == "2":
                    dpadInputs[direction] = f'JOYCODE_{joycode}_HAT1RIGHT'
                if pad.inputs[direction].value == "4":
                    dpadInputs[direction] = f'JOYCODE_{joycode}_HAT1DOWN'
                if pad.inputs[direction].value == "8":
                    dpadInputs[direction] = f'JOYCODE_{joycode}_HAT1LEFT'
            else:
                dpadInputs[direction] = ''
        buttonDirections: dict[str, str] = {}
        # workarounds for issue #6892
        # Modified because right stick to buttons was not working after the workaround
        # Creates a blank, only modifies if the button exists in the pad.
        # Button assigment modified - blank "OR" gets removed by MAME if the button is undefined.
        for direction in ['a', 'b', 'x', 'y']:
            buttonDirections[direction] = ''
            if direction in pad.inputs:
                if pad.inputs[direction].type == 'button':
                    buttonDirections[direction] = f'JOYCODE_{joycode}_BUTTON{int(pad.inputs[direction].id)+1}'

        if ignoreAxis and dpadInputs['up'] and dpadInputs['down'] and dpadInputs['left'] and dpadInputs['right']:
            if key == "joystick1up" or key == "up":
                return dpadInputs['up']
            if key == "joystick1down" or key == "down":
                return dpadInputs['down']
            if key == "joystick1left" or key == "left":
                return dpadInputs['left']
            if key == "joystick1right" or key == "right":
                return dpadInputs['right']
        if altButtons == "qbert": # Q*Bert Joystick
            if key == "joystick1up" or key == "up":
                return f"JOYCODE_{joycode}_YAXIS_UP_SWITCH JOYCODE_{joycode}_XAXIS_RIGHT_SWITCH OR {dpadInputs['up']} {dpadInputs['right']}"
            if key == "joystick1down" or key == "down":
                return f"JOYCODE_{joycode}_YAXIS_DOWN_SWITCH JOYCODE_{joycode}_XAXIS_LEFT_SWITCH OR {dpadInputs['down']} {dpadInputs['left']}"
            if key == "joystick1left" or key == "left":
                return f"JOYCODE_{joycode}_XAXIS_LEFT_SWITCH JOYCODE_{joycode}_YAXIS_UP_SWITCH OR {dpadInputs['left']} {dpadInputs['up']}"
            if key == "joystick1right" or key == "right":
                return f"JOYCODE_{joycode}_XAXIS_RIGHT_SWITCH JOYCODE_{joycode}_YAXIS_DOWN_SWITCH OR {dpadInputs['right']} {dpadInputs['down']}"
        else:
            if key == "joystick1up" or key == "up":
                return f"JOYCODE_{joycode}_YAXIS_UP_SWITCH OR {dpadInputs['up']}"
            if key == "joystick1down" or key == "down":
                return f"JOYCODE_{joycode}_YAXIS_DOWN_SWITCH OR {dpadInputs['down']}"
            if key == "joystick1left" or key == "left":
                return f"JOYCODE_{joycode}_XAXIS_LEFT_SWITCH OR {dpadInputs['left']}"
            if key == "joystick1right" or key == "right":
                return f"JOYCODE_{joycode}_XAXIS_RIGHT_SWITCH OR {dpadInputs['right']}"
        # Fix for the workaround
        for direction in pad.inputs:
            if(key == "joystick2up"):
                return f"JOYCODE_{joycode}_RYAXIS_NEG_SWITCH OR {buttonDirections['x']}"
            if(key == "joystick2down"):
                return f"JOYCODE_{joycode}_RYAXIS_POS_SWITCH OR {buttonDirections['b']}"
            if(key == "joystick2left"):
                return f"JOYCODE_{joycode}_RXAXIS_NEG_SWITCH OR {buttonDirections['y']}"
            if(key == "joystick2right"):
                return f"JOYCODE_{joycode}_RXAXIS_POS_SWITCH OR {buttonDirections['a']}"
            if int(input.id) in mameAxisMappingNames:
                idname = mameAxisMappingNames[int(input.id)]
                return f"JOYCODE_{joycode}_{idname}_POS_SWITCH"

    return "unknown"

def hasStick(pad: Controller) -> bool:
    return "joystick1up" in pad.inputs

def getRoot(config: minidom.Document, name: str):
    xml_section = config.getElementsByTagName(name)

    if len(xml_section) == 0:
        xml_section = config.createElement(name)
        config.appendChild(xml_section)
    else:
        xml_section = xml_section[0]

    return xml_section

def getSection(config: minidom.Document, xml_root: minidom.Element, name: str):
    xml_section = xml_root.getElementsByTagName(name)

    if len(xml_section) == 0:
        xml_section = config.createElement(name)
        xml_root.appendChild(xml_section)
    else:
        xml_section = xml_section[0]

    return xml_section

def removeSection(config: minidom.Document, xml_root: minidom.Element, name: str):
    xml_section = xml_root.getElementsByTagName(name)

    for i in range(0, len(xml_section)):
        old = cast(minidom.Element, xml_root.removeChild(xml_section[i]))
        old.unlink()

def addCommonPlayerPorts(config: minidom.Document, xml_input: minidom.Element, nplayer: int):
    # adstick for guns
    for axis in ["X", "Y"]:
        nanalog = 1 if axis == "X" else 2
        xml_port = config.createElement("port")
        xml_port.setAttribute("tag", f":mainpcb:ANALOG{nanalog}")
        xml_port.setAttribute("type", f"P{nplayer}_AD_STICK_{axis}")
        xml_port.setAttribute("mask", "255")
        xml_port.setAttribute("defvalue", "128")
        xml_newseq = config.createElement("newseq")
        xml_newseq.setAttribute("type", "standard")
        xml_port.appendChild(xml_newseq)
        value = config.createTextNode(f"GUNCODE_{nplayer}_{axis}AXIS")
        xml_newseq.appendChild(value)
        xml_input.appendChild(xml_port)
