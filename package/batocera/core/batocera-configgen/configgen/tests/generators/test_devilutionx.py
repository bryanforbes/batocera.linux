from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.devilutionx.devilutionxGenerator import DevilutionXGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestDevilutionXGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DevilutionXGenerator]:
        return DevilutionXGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'devilutionx'

    @pytest.fixture
    def emulator(self) -> str:
        return 'devilutionx'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'devilutionx_stretch': 'false'}, 4 / 3),
            ({'devilutionx_stretch': 'true'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: DevilutionXGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: DevilutionXGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'devilutionx' / 'diablo.mpq',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'devilutionx').is_dir()
        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: DevilutionXGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'devilutionx' / 'diablo.ini',
            contents="""[Graphics]
foo = 1

[Something]
bar = 0
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'devilutionx' / 'diablo.mpq',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'devilutionx_stretch': 'true'},
            {'devilutionx_stretch': 'false'},
            {'showFPS': 'true'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: DevilutionXGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'devilutionx' / 'diablo.mpq',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom',
        [
            'hellfire.mpq',
            'spawn.mpq',
            'foo.mpq',
        ],
    )
    def test_generate_rom(
        self,
        generator: DevilutionXGenerator,
        rom: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'devilutionx' / f'{rom}',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
