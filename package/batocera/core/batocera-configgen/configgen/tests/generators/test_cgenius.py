from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.cgenius.cgeniusGenerator import CGeniusGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


class TestCGeniusGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[CGeniusGenerator]:
        return CGeniusGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'cgenius'

    @pytest.fixture
    def emulator(self) -> str:
        return 'cgenius'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(ROMS / 'cgenius')

        return fs

    def test_get_mouse_mode(self, generator: CGeniusGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'cgenius_aspect': '5:4'}, 4 / 3),
            ({'cgenius_aspect': '16:9'}, 16 / 9),
            ({'cgenius_aspect': '16:10'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: CGeniusGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: CGeniusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'cgenius' / 'rom.cgenius',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'cgenius' / 'cgenius.cfg').read_text() == (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text()

    def test_generate_existing(
        self,
        generator: CGeniusGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'cgenius' / 'cgenius.cfg',
            contents="""[FileHandling]
EnableLogfile = false
SearchPath1 = /userdata/roms/cgenius
SearchPath2 = /userdata/roms/cgenius/games
[Video]
aspect = 4:3
fullscreen = false
integerScaling = false
filter = none
OGLfilter = nearest
gameHeight = 200
gameWidth = 320
ShowCursor = false
[input0]
Fire = Joy0-B3
Jump = Joy0-B2
Down = Joy0-H1
Left = Joy0-H7
Run = Joy0-B4
Camlead = Joy0-B8
Right = Joy0-H3
Up = Joy0-H3
Status = Joy0-B1
Pogo = Joy0-B9
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'cgenius' / 'rom.cgenius',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'cgenius' / 'cgenius.cfg').read_text() == (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cgenius_aspect': '16:9'},
            {'cgenius_filter': 1},
            {'cgenius_quality': 'best'},
            {'cgenius_render': '200'},
            {'cgenius_render': '240'},
            {'cgenius_render': '360'},
            {'cgenius_render': '480'},
            {'cgenius_cursor': 'true'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: CGeniusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'cgenius' / 'rom.cgenius',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'cgenius' / 'cgenius.cfg').read_text() == (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text()

    def test_generate_controllers(
        self,
        generator: CGeniusGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'cgenius' / 'rom.cgenius',
                [
                    generic_xbox_pad.replace(
                        player_number=n, index=n - 1, real_name=f'real name {n}', device_path=f'/dev/input/event{n}'
                    )
                    for n in range(1, 6)
                ],
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'cgenius' / 'cgenius.cfg').read_text() == (CONFIGS / 'cgenius' / 'cgenius.cfg').read_text()
