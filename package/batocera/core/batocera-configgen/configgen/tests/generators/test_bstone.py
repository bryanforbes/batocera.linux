from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.bstone.bstoneGenerator import BstoneGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestBstoneGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[BstoneGenerator]:
        return BstoneGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'bstone'

    @pytest.fixture
    def emulator(self) -> str:
        return 'bstone'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'bstone_widescreen': '0'}, 4 / 3),
            ({'bstone_widescreen': '1'}, 16 / 9),
            ({'bstone_ui_stretched': '0'}, 4 / 3),
            ({'bstone_ui_stretched': '1'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: BstoneGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    @pytest.mark.parametrize(
        ('game_name', 'extension'),
        [
            ('Aliens of Gold (Shareware)', 'bs1'),
            ('Aliens of Gold', 'bs6'),
            ('Planet Strike', 'vsi'),
        ],
    )
    def test_generate(
        self,
        fs: FakeFilesystem,
        generator: BstoneGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        game_name: str,
        extension: str,
    ) -> None:
        fs.create_file(ROMS / 'bstone' / game_name / f'{game_name}.bstone')
        fs.create_file(ROMS / 'bstone' / game_name / f'audiohed.{extension}')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'bstone' / game_name / f'{game_name}.bstone',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'bstone' / 'bstone_config.txt').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        generator: BstoneGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'bstone' / 'Aliens of Gold' / 'Aliens of Gold.bstone')
        fs.create_file(ROMS / 'bstone' / 'Aliens of Gold' / 'audiohed.bs6')
        fs.create_file(
            CONFIGS / 'bstone' / 'bstone_config.txt',
            contents="""
foo_bar "baz"
vid_width "640"
vid_height "480"
vid_is_vsync "1"
vid_is_ui_stretched "1"
ham_spam "blam"
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'bstone' / 'Aliens of Gold' / 'Aliens of Gold.bstone',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'bstone' / 'bstone_config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'bstone_widescreen': '0'},
            {'bstone_widescreen': '1'},
            {'bstone_vsync': '0'},
            {'bstone_vsync': '1'},
            {'bstone_ui_stretched': '0'},
            {'bstone_ui_stretched': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        fs: FakeFilesystem,
        generator: BstoneGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'bstone' / 'Aliens of Gold' / 'Aliens of Gold.bstone')
        fs.create_file(ROMS / 'bstone' / 'Aliens of Gold' / 'audiohed.bs6')

        generator.generate(
            mock_system,
            ROMS / 'bstone' / 'Aliens of Gold' / 'Aliens of Gold.bstone',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'bstone' / 'bstone_config.txt').read_text() == snapshot(name='config')
