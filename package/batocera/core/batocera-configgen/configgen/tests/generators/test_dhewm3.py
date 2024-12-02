from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.dhewm3.dhewm3Generator import Dhewm3Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestDhewm3Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Dhewm3Generator]:
        return Dhewm3Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'dhewm3'

    @pytest.fixture
    def emulator(self) -> str:
        return 'dhewm3'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/userdata/roms/doom3/rom.d3', contents='base/pak000.pk4')

        return fs

    def test_get_in_game_ratio(self, generator: Dhewm3Generator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Dhewm3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'doom3' / 'rom.d3',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: Dhewm3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg',
            contents="""seta r_mode "-1"
seta r_fullscreen "0"
seta r_customHeight "640"
seta r_customWidth "480"
bind "JOY_BTN_SOUTH" "_moveUp"
bind "JOY_BTN_EAST" "_moveDown"
bind "JOY_BTN_WEST" "_impulse19"
bind "JOY_BTN_NORTH" "_impulse13"
bind "JOY_BTN_LSTICK" "_strafe"
bind "JOY_BTN_RSTICK" "_speed"
bind "JOY_BTN_LSHOULDER" "_impulse15"
bind "JOY_BTN_RSHOULDER" "_impulse14"
bind "JOY_STICK1_UP" "_forward"
bind "JOY_STICK1_DOWN" "_back"
bind "JOY_STICK1_LEFT" "_moveLeft"
bind "JOY_STICK1_RIGHT" "_moveRight"
bind "JOY_STICK2_UP" "_lookUp"
bind "JOY_STICK2_DOWN" "_lookDown"
bind "JOY_STICK2_LEFT" "_left"
bind "JOY_STICK2_RIGHT" "_right"
bind "JOY_TRIGGER2" "_attack"
seta sys_lang "english"
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'doom3' / 'rom.d3',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg').read_text() == snapshot(name='config')

    def test_generate_d3xp(
        self,
        generator: Dhewm3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        Path('/userdata/roms/doom3/rom.d3').write_text('d3xp/pak000.pk4')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'doom3' / 'rom.d3',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dhewm3' / 'd3xp' / 'dhewm.cfg').read_text() == (
            CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg'
        ).read_text()

    @pytest.mark.parametrize('mod_directory', ['perfected_roe', 'sikkmodd3xp', 'd3le'])
    def test_generate_mods(
        self,
        generator: Dhewm3Generator,
        mod_directory: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        Path('/userdata/roms/doom3/rom.d3').write_text(f'{mod_directory}/pak000.pk4')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'doom3' / 'rom.d3',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dhewm3' / mod_directory / 'dhewm.cfg').read_text() == (
            CONFIGS / 'dhewm3' / mod_directory / 'dhewm.cfg'
        ).read_text()

    @pytest.mark.parametrize(
        'mock_system_config', [{'dhewm3_brightness': 1.60}, {'dhewm3_language': 'spanish'}], ids=str
    )
    def test_generate_config(
        self,
        generator: Dhewm3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'doom3' / 'rom.d3',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dhewm3' / 'base' / 'dhewm.cfg').read_text() == snapshot()
