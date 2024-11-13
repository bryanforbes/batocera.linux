from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...Emulator import Emulator
    from ...utils.configparser import CaseSensitiveConfigParser


# return true if the option is considered defined
def defined(key: str, dict: dict[str, Any]) -> bool:
    return key in dict and isinstance(dict[key], str) and len(dict[key]) > 0

def updateFBAConfig(iniConfig: CaseSensitiveConfigParser, system: Emulator) -> None:
    ratioIndexes = {'4/3': '0', '16/9': '1'}

    if not iniConfig.has_section("Graphics"):
        iniConfig.add_section("Graphics")

    iniConfig.set("Graphics", "DisplaySmoothStretch", system.get_option_bool("smooth", return_values=("1", "0")))
    iniConfig.set("Graphics", "MaintainAspectRatio", ratioIndexes.get(system.get_option_str("ratio", "None"), "0"))
    iniConfig.set("Graphics", "DisplayEffect", "1" if system.get_option_str("shaders") == "scanlines" else "0")
    iniConfig.set("Graphics", "RotateScreen",  "0")
    iniConfig.set("Graphics", "DisplayBorder", "0")
