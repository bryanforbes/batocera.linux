from __future__ import annotations

from typing import TYPE_CHECKING

from ... import Command
from ..Generator import Generator

if TYPE_CHECKING:
    from ...types import HotkeysContext

class SteamGenerator(Generator):

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        gameId = None
        if rom.name != "Steam.steam":
            # read the id inside the file
            gameId = rom.read_text().strip()

        commandArray = ["batocera-steam"] if gameId is None else ["batocera-steam", gameId]
        return Command.Command(array=commandArray)

    def getMouseMode(self, config, rom):
        return True

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "steam",
            "keys": { "exit": ["KEY_LEFTALT", "KEY_F4"] }
        }
