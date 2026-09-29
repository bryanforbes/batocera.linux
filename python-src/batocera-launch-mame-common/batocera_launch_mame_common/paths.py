from __future__ import annotations

from pathlib import Path
from typing import Final

from batocera_common.dataclasses import cached_dataclass, cached_property
from batocera_common.paths import BIOS, CHEATS, CONFIGS, ROMS, SAVES
from batocera_launch.paths import LAUNCH_DATA_DIR

MAME_BIN_DIR: Final = Path('/usr/bin/mame')
MAME_DATA_DIR: Final = LAUNCH_DATA_DIR / 'mame'


@cached_dataclass
class MAMEPathsMixin:
    @cached_property
    def roms_dir(self) -> Path:
        return ROMS / 'mame'

    @cached_property
    def bios_dir(self) -> Path:
        return BIOS / 'mame'

    @cached_property
    def config_dir(self) -> Path:
        return CONFIGS / 'mame'

    @cached_property
    def saves_dir(self) -> Path:
        return SAVES / 'mame'

    @cached_property
    def cheats_dir(self) -> Path:
        return CHEATS / 'mame'
