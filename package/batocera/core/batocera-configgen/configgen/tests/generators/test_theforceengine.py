from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.theforceengine.theforceengineGenerator import TheForceEngineGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestTheForceEngineGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TheForceEngineGenerator]:
        return TheForceEngineGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'theforceengine'

    @pytest.fixture
    def emulator(self) -> str:
        return 'theforceengine'

    def test_get_mouse_mode(self, generator: TheForceEngineGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'force_widescreen': '0'}, 4 / 3),
            ({'force_widescreen': '1'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: TheForceEngineGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: TheForceEngineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'theforceengine' / 'rom.tfe')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'theforceengine' / 'rom.tfe',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'theforceengine' / 'settings.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: TheForceEngineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'theforceengine' / 'rom.tfe')
        fs.create_file(
            CONFIGS / 'theforceengine' / 'settings.ini',
            contents="""[Window]
fullscreen = false

[Graphics]
widescreen = true

[Hud]
scale = 2.00

[Enhancements]
hdTextures = 1

[Sound]
disableSoundInMenus = true

[System]

[A11y]

[Game]
game = Foo

[Dark_Forces]
sourcePath = "/userdata/roms/theforceengine/Blah/"

[Outlaws]
sourcePath = "/tmp"

[CVar]

[Spam]
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'theforceengine' / 'rom.tfe',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'theforceengine' / 'settings.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'force_render_res': '200'},
            {'force_widescreen': '1'},
            {'force_vsync': '0'},
            {'force_vsync': '1'},
            {'force_rate': '30'},
            {'force_api': '0'},
            {'force_api': '1'},
            {'force_colour': '2'},
            {'force_bilinear': '0'},
            {'force_bilinear': '1'},
            {'force_mipmapping': '0'},
            {'force_mipmapping': '1'},
            {'force_crosshair': '0'},
            {'force_crosshair': '1'},
            {'force_postfx': '0'},
            {'force_postfx': '1'},
            {'force_hd': '0'},
            {'force_hd': '1'},
            {'force_menu_sound': '0'},
            {'force_menu_sound': '1'},
            {'force_digital_audio': '0'},
            {'force_digital_audio': '1'},
            {'force_fight_music': '0'},
            {'force_fight_music': '1'},
            {'force_auto_aim': '0'},
            {'force_auto_aim': '1'},
            {'force_secret_msg': '0'},
            {'force_secret_msg': '1'},
            {'force_auto_run': '0'},
            {'force_auto_run': '1'},
            {'force_boba': '0'},
            {'force_boba': '1'},
            {'force_smooth_vues': '0'},
            {'force_smooth_vues': '1'},
            {'force_skip_cutscenes': 'show'},
            {'force_skip_cutscenes': 'initial'},
            {'force_skip_cutscenes': 'skip'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: TheForceEngineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'theforceengine' / 'rom.tfe')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'theforceengine' / 'rom.tfe',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'theforceengine' / 'settings.ini').read_text() == snapshot(name='config')

    def test_generate_mod(
        self,
        generator: TheForceEngineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'theforceengine' / 'rom.tfe')
        fs.create_file(CONFIGS / 'theforceengine' / 'Mods' / 'df_patch4.zip')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'theforceengine' / 'rom.tfe',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_tfe_file(
        self,
        generator: TheForceEngineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'theforceengine' / 'Mods' / 'df_patch4.zip')
        fs.create_file(ROMS / 'theforceengine' / 'rom.tfe', contents='other.zip')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'theforceengine' / 'rom.tfe',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
