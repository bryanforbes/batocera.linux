from __future__ import annotations

from typing import TYPE_CHECKING

from ... import Command
from ...batoceraPaths import CONFIGS
from ..Generator import Generator

if TYPE_CHECKING:
    from ...types import HotkeysContext


class DosBoxGenerator(Generator):

    # Main entry of the module
    # Return command
    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        # Find rom path
        batFile = rom / "dosbox.bat"
        gameConfFile = rom / "dosbox.cfg"

        commandArray = [
            '/usr/bin/dosbox',
            "-fullscreen",
            "-userconf",
            "-exit",
            batFile,
            "-c", f"""set ROOT={rom}"""
        ]
        if gameConfFile.is_file():
            commandArray.append("-conf")
            commandArray.append(gameConfFile)
        else:
            commandArray.append("-conf")
            commandArray.append(CONFIGS / 'dosbox' / 'dosbox.conf')

        return Command.Command(array=commandArray)

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "dosbox",
            "keys": { "exit": ["KEY_LEFTCTRL", "KEY_F9"] }
        }
