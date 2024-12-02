from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.openmohaa.openmohaaGenerator import OpenMOHAAGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestOpenMOHAAGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenMOHAAGenerator]:
        return OpenMOHAAGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'mohaa'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openmohaa'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(ROMS / 'mohaa')
        return fs

    def test_get_mouse_mode(self, generator: OpenMOHAAGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: OpenMOHAAGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    @pytest.mark.parametrize(
        'rom',
        [
            'Medal of Honor - Allied Assault.mohaa',
            'Medal of Honor - Allied Assault - Breakthrough.mohaa',
            'Medal of Honor - Allied Assault - Spearhaed.mohaa',
        ],
    )
    def test_generate(
        self,
        generator: OpenMOHAAGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mohaa' / rom,
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        config_dir = 'mainta' if 'spear' in rom.lower() else 'maintt' if 'break' in rom.lower() else 'main'
        assert (CONFIGS / 'openmohaa' / config_dir / 'configs' / 'omconfig.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom',
        [
            'Medal of Honor - Allied Assault.mohaa',
            'Medal of Honor - Allied Assault - Breakthrough.mohaa',
            'Medal of Honor - Allied Assault - Spearhaed.mohaa',
        ],
    )
    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        generator: OpenMOHAAGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        config_dir = 'mainta' if 'spear' in rom.lower() else 'maintt' if 'break' in rom.lower() else 'main'
        fs.create_file(
            CONFIGS / 'openmohaa' / config_dir / 'configs' / 'omconfig.cfg',
            contents="""seta r_mode "-1"
seta r_fullscreen "1"
seta r_allowResize "0"
seta r_centerWindow "1"
seta r_customheight ""480""
seta r_customwidth ""1280""
seta r_colorbits "0"
seta r_picmip "1"
seta r_texturebits "0"
seta r_textureMode "gl_linear_mipmap_linear"
seta ui_crosshair "0"
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'mohaa' / rom,
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openmohaa' / config_dir / 'configs' / 'omconfig.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'mohaa_colour': '0'},
            {'mohaa_colour': '16'},
            {'mohaa_texture': '2'},
            {'mohaa_texture': '1'},
            {'mohaa_texture_colour': '0'},
            {'mohaa_texture_colour': '16'},
            {'mohaa_texture_filter': 'GL_LINEAR_MIPMAP_NEAREST'},
            {'mohaa_texture_filter': 'gl_linear_mipmap_linear'},
            {'mohaa_decals': '0'},
            {'mohaa_decals': '1'},
            {'mohaa_weather': '0'},
            {'mohaa_weather': '1'},
            {'mohaa_brightness': '2.42'},
            {'mohaa_compression': '0'},
            {'mohaa_compression': '1'},
            {'mohaa_view': '0'},
            {'mohaa_view': '2'},
            {'mohaa_shadows': '0'},
            {'mohaa_shadows': '1'},
            {'mohaa_terrain': '0'},
            {'mohaa_terrain': '1'},
            {'mohaa_terrain': '2'},
            {'mohaa_terrain': '3'},
            {'mohaa_model': '0'},
            {'mohaa_model': '1'},
            {'mohaa_model': '2'},
            {'mohaa_model': '3'},
            {'mohaa_model': '4'},
            {'mohaa_model': '5'},
            {'mohaa_effects': '0'},
            {'mohaa_effects': '1'},
            {'mohaa_effects': '2'},
            {'mohaa_effects': '3'},
            {'mohaa_effects': '4'},
            {'mohaa_effects': '5'},
            {'mohaa_effects': '6'},
            {'mohaa_curve': '0'},
            {'mohaa_curve': '1'},
            {'mohaa_curve': '2'},
            {'mohaa_curve': '3'},
            {'mohaa_subtitles': '0'},
            {'mohaa_subtitles': '1'},
            {'mohaa_dynamic_lighting': '0'},
            {'mohaa_dynamic_lighting': '1'},
            {'mohaa_entity_lighting': '0'},
            {'mohaa_entity_lighting': '1'},
            {'mohaa_smoke': '0'},
            {'mohaa_smoke': '1'},
            {'mohaa_weapons': '0'},
            {'mohaa_weapons': '1'},
            {'mohaa_crosshair': '0'},
            {'mohaa_crosshair': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: OpenMOHAAGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'mohaa' / 'Medal of Honor - Allied Assault.mohaa',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openmohaa' / 'main' / 'configs' / 'omconfig.cfg').read_text() == snapshot(name='config')
