from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.exceptions import BatoceraException
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('superbroswar')
class TestLibretroGeneratorSuperBrosWar(LibretroBaseCoreTest):
    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        for dir in [
            'music/world/Standard',
            'music/game/Standard/Special',
            'music/game/Standard/Menu',
            'filters',
            'worlds/KingdomHigh',
            'worlds/MrIsland',
            'worlds/Sky World',
            'worlds/Smb3',
            'worlds/Simple',
            'worlds/screenshots',
            'worlds/Flurry World',
            'worlds/MixedRiver',
            'worlds/Contest',
            'gfx/skins',
            'gfx/packs/Retro/fonts',
            'gfx/packs/Retro/modeobjects',
            'gfx/packs/Retro/eyecandy',
            'gfx/packs/Retro/awards',
            'gfx/packs/Retro/powerups',
            'gfx/packs/Retro/menu',
            'gfx/packs/Classic/projectiles',
            'gfx/packs/Classic/fonts',
            'gfx/packs/Classic/modeobjects',
            'gfx/packs/Classic/world',
            'gfx/packs/Classic/world/thumbnail',
            'gfx/packs/Classic/world/preview',
            'gfx/packs/Classic/modeskins',
            'gfx/packs/Classic/hazards',
            'gfx/packs/Classic/blocks',
            'gfx/packs/Classic/backgrounds',
            'gfx/packs/Classic/tilesets/SMB2',
            'gfx/packs/Classic/tilesets/Expanded',
            'gfx/packs/Classic/tilesets/SMB1',
            'gfx/packs/Classic/tilesets/Classic',
            'gfx/packs/Classic/tilesets/SMB3',
            'gfx/packs/Classic/tilesets/SuperMarioWorld',
            'gfx/packs/Classic/tilesets/YoshisIsland',
            'gfx/packs/Classic/eyecandy',
            'gfx/packs/Classic/awards',
            'gfx/packs/Classic/powerups',
            'gfx/packs/Classic/menu',
            'gfx/leveleditor',
            'gfx/docs',
            'sfx/packs/Classic',
            'sfx/announcer/Mario',
            'maps/tour',
            'maps/cache',
            'maps/screenshots',
            'maps/special',
            'tours',
        ]:
            fs.create_dir(f'/userdata/roms/superbroswar/{dir}')

        return fs

    def test_generate_missing_assets(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        shutil.rmtree(ROMS / mock_system.name)
        fs.create_file(ROMS / mock_system.name / 'rom.game')

        with pytest.raises(
            BatoceraException,
            match=r'^Game assets not installed. You can get them from the Batocera Content Downloader.$',
        ):
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
