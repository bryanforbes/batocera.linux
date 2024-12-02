from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.fallout2.fallout2Generator import Fallout2Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestFallout2Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Fallout2Generator]:
        return Fallout2Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'fallout2-ce'

    @pytest.fixture
    def emulator(self) -> str:
        return 'fallout2-ce'

    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(ROMS / 'fallout2-ce')
        fs.create_file('/usr/bin/fallout2-ce', contents='fallout bin')

        return fs

    def test_get_mouse_mode(self, generator: Fallout2Generator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: Fallout2Generator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Fallout2Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path(),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert filecmp.cmp('/usr/bin/fallout2-ce', ROMS / 'fallout2-ce' / 'fallout2-ce')
        assert (CONFIGS / 'fallout2' / 'fallout2.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'fallout2' / 'f2_res.ini').read_text() == snapshot(name='ini')

    def test_generate_existing(
        self,
        generator: Fallout2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'fallout2' / 'fallout2.cfg',
            contents="""[debug]
debug = 1

[preferences]
game_difficulty = 4

[sound]
music_path1 = DATA/SOUND/MUSIC/Extra

[system]
language = greek
""",
        )
        fs.create_file(
            CONFIGS / 'fallout2' / 'f2_res.ini',
            contents="""[MAIN]
SCALE_2X = 0
""",
        )
        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fallout2' / 'fallout2.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'fallout2' / 'f2_res.ini').read_text() == snapshot(name='ini')

    def test_generate_existing_src_config(
        self,
        generator: Fallout2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'fallout2-ce' / 'fallout2.cfg',
            contents="""[debug]
debug = 1

[preferences]
game_difficulty = 4

[sound]
music_path1 = DATA/SOUND/MUSIC/Extra

[system]
language = greek
""",
        )
        fs.create_file(
            ROMS / 'fallout2-ce' / 'f2_res.ini',
            contents="""[MAIN]
SCALE_2X = 0
""",
        )

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fallout2' / 'fallout2.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'fallout2' / 'f2_res.ini').read_text() == snapshot(name='ini')

    def test_generate_existing_exe(
        self,
        generator: Fallout2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(ROMS / 'fallout2-ce' / 'fallout2-ce', contents='new fallout bin')

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'fallout2-ce' / 'fallout2-ce').read_text() == 'new fallout bin'

    def test_generate_existing_old_exe(
        self,
        generator: Fallout2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(ROMS / 'fallout2-ce' / 'fallout2-ce', contents='old fallout bin')
        fs.utime(str(ROMS / 'fallout2-ce' / 'fallout2-ce'), (0, 0))

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'fallout2-ce' / 'fallout2-ce').read_text() == 'fallout bin'

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'fout2_game_difficulty': '0'},
            {'fout2_combat_difficulty': '0'},
            {'fout2_violence_level': '0'},
            {'fout2_subtitles': '1'},
            {'fout2_language': 'french'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Fallout2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fallout2' / 'fallout2.cfg').read_text() == snapshot

    def test_generate_resolution(
        self,
        generator: Fallout2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1024, 'height': 768},
        )

        assert (CONFIGS / 'fallout2' / 'f2_res.ini').read_text() == snapshot
