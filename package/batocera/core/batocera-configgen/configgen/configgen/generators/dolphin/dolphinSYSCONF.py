#!/usr/bin/env python

from __future__ import annotations

import logging
from os import environ
from struct import pack, unpack
from typing import TYPE_CHECKING, BinaryIO, Literal

from ...utils.logger import setup_logging
from .dolphinPaths import DOLPHIN_SAVES

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from ...Emulator import Emulator
    from ...types import Resolution


_logger = logging.getLogger(__name__)

def readBEInt16(f: BinaryIO) -> int:
    data = f.read(2)
    unpacked = unpack(">H", data)
    return unpacked[0]

def readBEInt32(f: BinaryIO) -> int:
    data = f.read(4)
    unpacked = unpack(">L", data)
    return unpacked[0]

def readBEInt64(f: BinaryIO) -> int:
    data = f.read(8)
    unpacked = unpack(">Q", data)
    return unpacked[0]

def readBytes(f: BinaryIO, x: int) -> bytes:
    return f.read(x)

def readString(f: BinaryIO, x: int) -> str:
    data = f.read(x)
    decodedbytes = data.decode('utf-8')
    return str(decodedbytes)

def readInt8(f: BinaryIO) -> int:
    data = f.read(1)
    unpacked = unpack("B", data)
    return unpacked[0]

def writeInt8(f: BinaryIO, x: int) -> None:
    data = pack("B", x)
    f.write(data)

def readWriteEntry(f: BinaryIO, setval: Mapping[str, int]) -> None:
    itemHeader     = readInt8(f)
    itemType       = (itemHeader & 0xe0) >> 5
    itemNameLength = (itemHeader & 0x1f) + 1
    itemName       = readString(f, itemNameLength)

    if itemName in setval:
        if itemType == 3: # byte
            itemValue = setval[itemName]
            writeInt8(f, itemValue)
        else:
            raise Exception(f"not writable type {itemType}")
    else:
        if itemType == 1: # big array
            dataSize = readBEInt16(f) + 1
            readBytes(f, dataSize)
            itemValue = "[Big Array]"
        elif itemType == 2: # small array
            dataSize = readInt8(f) + 1
            readBytes(f, dataSize)
            itemValue = "[Small Array]"
        elif itemType == 3: # byte
            itemValue = readInt8(f)
        elif itemType == 4: # short
            itemValue = readBEInt16(f)
        elif itemType == 5: # long
            itemValue = readBEInt32(f)
        elif itemType == 6: # long long
            itemValue = readBEInt64(f)
        elif itemType == 7: # bool
            itemValue = readInt8(f)
        else:
            raise Exception(f"unknown type {itemType}")

    if not setval or itemName in setval:
        _logger.debug('%12s = %s', itemName, itemValue)

def readWriteFile(filepath: Path, setval: Mapping[str, int]) -> None:
    # open in read read/write depending of the action
    with filepath.open("r+b" if setval else "rb") as f:
        _ = readString(f, 4) # read SCv0
        numEntries = readBEInt16(f)   # num entries
        offsetSize = (numEntries+1)*2 # offsets
        readBytes(f, offsetSize)

        for _ in range(numEntries): # entries
            readWriteEntry(f, setval)

def getWiiLangFromEnvironment() -> int:
    lang = environ['LANG'][:5]
    availableLanguages = { "jp_JP": 0, "en_US": 1, "de_DE": 2,
                           "fr_FR": 3, "es_ES": 4, "it_IT": 5,
                           "nl_NL": 6, "zh_CN": 7, "zh_TW": 8, "ko_KR": 9 }

    if lang in availableLanguages:
        return availableLanguages[lang]

    return availableLanguages["en_US"]

def getRatioFromConfig(config: dict[str, object], gameResolution: Resolution) -> Literal[0, 1]:
    # Sets the setting available to the Wii's internal NAND. Only has two values:
    # 0: 4:3 ; 1: 16:9
    return 1 if config.get("tv_mode") == "1" else 0

def getSensorBarPosition(system: Emulator) -> Literal[0, 1]:
    # Sets the setting available to the Wii's internal NAND. Only has two values:
    # 0: BOTTOM ; 1: TOP
    return 1 if system.get_option("sensorbar_position") == "1" else 0

def update(system: Emulator, filepath: Path, gameResolution: Resolution) -> None:
    arg_setval = {
        "IPL.LNG": getWiiLangFromEnvironment(),
        "IPL.AR": getRatioFromConfig(system.config, gameResolution),
        "BT.BAR": getSensorBarPosition(system)
    }
    readWriteFile(filepath, arg_setval)

if __name__ == '__main__':
    with setup_logging():
        readWriteFile(DOLPHIN_SAVES / "Wii" / "shared2" / "sys" / "SYSCONF", {})
