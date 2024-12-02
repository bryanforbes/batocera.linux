from __future__ import annotations

import filecmp
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.openjkdf2.openjkdf2Generator import OpenJKDF2Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestOpenJKDF2GeneratorGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenJKDF2Generator]:
        return OpenJKDF2Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'jkdf2'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openjkdf2'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/openjkdf2', contents='openjkdf2')

        return fs

    def test_get_mouse_mode(self, generator: OpenJKDF2Generator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 16 / 9),
            ({'jkdf2_aspect': '0'}, 16 / 9),
            ({'jkdf2_aspect': '1'}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: OpenJKDF2Generator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'jkdf2' / 'game')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'jkdf2' / 'game' / 'rom.jedi',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert filecmp.cmp(
            ROMS / 'jkdf2' / 'game' / 'openjkdf2',
            '/usr/bin/openjkdf2',
        )
        assert stat.filemode((ROMS / 'jkdf2' / 'game' / 'openjkdf2').stat().st_mode) == snapshot(name='filemode')
        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'openjkdf2.json').read_text() == snapshot(
            name='config'
        )
        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'openjkdf2_cvars.json').read_text() == snapshot(
            name='cvars'
        )
        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'Batocera.plr').read_text() == snapshot(name='plr')

    def test_generate_existing_binary(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'jkdf2' / 'game' / 'openjkdf2', contents='old binary')

        generator.generate(
            mock_system,
            ROMS / 'jkdf2' / 'game' / 'rom.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'jkdf2' / 'game' / 'openjkdf2').read_text() == 'old binary'
        assert stat.filemode((ROMS / 'jkdf2' / 'game' / 'openjkdf2').stat().st_mode) == snapshot(name='filemode')

    def test_generate_existing_old_binary(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'jkdf2' / 'game' / 'openjkdf2', contents='old binary')
        fs.utime(str(ROMS / 'jkdf2' / 'game' / 'openjkdf2'), (0, 0))

        generator.generate(
            mock_system,
            ROMS / 'jkdf2' / 'game' / 'rom.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert filecmp.cmp(
            ROMS / 'jkdf2' / 'game' / 'openjkdf2',
            '/usr/bin/openjkdf2',
        )
        assert stat.filemode((ROMS / 'jkdf2' / 'game' / 'openjkdf2').stat().st_mode) == snapshot(name='filemode')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'jkdf2_start': 'False'},
            {'jkdf2_start': 'True'},
            {'jkdf2_saber_cross': 'False'},
            {'jkdf2_saber_cross': 'True'},
            {'jkdf2_fist_cross': 'False'},
            {'jkdf2_fist_cross': 'True'},
            {'jkdf2_waggle': '0'},
            {'jkdf2_waggle': '1'},
            {'jkdf2_cross_size': '2.40'},
            {'jkdf2_cross_line': '2.40'},
            {'jkdf2_fov_vert': '0'},
            {'jkdf2_fov_vert': '1'},
            {'jkdf2_aspect': 'False'},
            {'jkdf2_aspect': 'True'},
            {'jkdf2_vsync': 'False'},
            {'jkdf2_vsync': 'True'},
            {'jkdf2_hidpi': 'False'},
            {'jkdf2_hidpi': 'True'},
            {'jkdf2_texture': 'False'},
            {'jkdf2_texture': 'True'},
            {'jkdf2_bloom': 'False'},
            {'jkdf2_bloom': 'True'},
            {'jkdf2_ssao': 'False'},
            {'jkdf2_ssao': 'True'},
            {'jkdf2_gamma': '2.00'},
            {'jkdf2_hud_scale': '1.60'},
            {'jkdf2_ssaa_multiple': '1.0'},
            {'jkdf2_ssaa_multiple': '2.0'},
            {'jkdf2_ssaa_multiple': '4.0'},
            {'jkdf2_corpses': 'False'},
            {'jkdf2_corpses': 'True'},
        ],
        ids=str,
    )
    def test_generate_config_json(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'jkdf2' / 'game')

        generator.generate(
            mock_system,
            ROMS / 'jkdf2' / 'game' / 'rom.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'openjkdf2.json').read_text() == snapshot(
            name='config'
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'jkdf2_start': 'False'},
            {'jkdf2_start': 'True'},
            {'jkdf2_saber_cross': 'False'},
            {'jkdf2_saber_cross': 'True'},
            {'jkdf2_fist_cross': 'False'},
            {'jkdf2_fist_cross': 'True'},
            {'jkdf2_waggle': '0'},
            {'jkdf2_waggle': '1'},
            {'jkdf2_cross_size': '2.40'},
            {'jkdf2_cross_line': '2.40'},
            {'jkdf2_fov_vert': '0'},
            {'jkdf2_fov_vert': '1'},
            {'jkdf2_aspect': 'False'},
            {'jkdf2_aspect': 'True'},
            {'jkdf2_vsync': 'False'},
            {'jkdf2_vsync': 'True'},
            {'jkdf2_hidpi': 'False'},
            {'jkdf2_hidpi': 'True'},
            {'jkdf2_texture': 'False'},
            {'jkdf2_texture': 'True'},
            {'jkdf2_bloom': 'False'},
            {'jkdf2_bloom': 'True'},
            {'jkdf2_ssao': 'False'},
            {'jkdf2_ssao': 'True'},
            {'jkdf2_gamma': '2.00'},
            {'jkdf2_hud_scale': '1.60'},
            {'jkdf2_ssaa_multiple': '1.0'},
            {'jkdf2_ssaa_multiple': '2.0'},
            {'jkdf2_ssaa_multiple': '4.0'},
            {'jkdf2_corpses': 'False'},
            {'jkdf2_corpses': 'True'},
        ],
        ids=str,
    )
    def test_generate_config_cvars(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'jkdf2' / 'game')

        generator.generate(
            mock_system,
            ROMS / 'jkdf2' / 'game' / 'rom.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'openjkdf2_cvars.json').read_text() == snapshot(
            name='cvars'
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'jkdf2_difficulty': '0'},
            {'jkdf2_difficulty': '1'},
            {'jkdf2_difficulty': '2'},
            {'jkdf2_scenes': '0'},
            {'jkdf2_scenes': '1'},
            {'jkdf2_subs': '0'},
            {'jkdf2_subs': '1'},
            {'jkdf2_map_rotate': '0'},
            {'jkdf2_map_rotate': '1'},
            {'jkdf2_aiming': '0'},
            {'jkdf2_aiming': '1'},
            {'jkdf2_crosshair': '0'},
            {'jkdf2_crosshair': '1'},
            {'jkdf2_saber_camera': '0'},
            {'jkdf2_saber_camera': '1'},
            {'jkdf2_pickup': '0'},
            {'jkdf2_pickup': '1'},
            {'jkdf2_dangerous': '0'},
            {'jkdf2_dangerous': '1'},
            {'jkdf2_weaker': '0'},
            {'jkdf2_weaker': '1'},
            {'jkdf2_saber': '0'},
            {'jkdf2_saber': '1'},
            {'jkdf2_switch': '0'},
            {'jkdf2_switch': '1'},
            {'jkdf2_switch_dangerous': '0'},
            {'jkdf2_switch_dangerous': '1'},
            {'jkdf2_reload': '0'},
            {'jkdf2_reload': '1'},
            {'jkdf2_reload_saber': '0'},
            {'jkdf2_reload_saber': '1'},
            {'jkdf2_pickup': '1', 'jkdf2_dangerous': '1', 'jkdf2_weaker': '1', 'jkdf2_saber': '1'},
            {'jkdf2_switch': '1', 'jkdf2_switch_dangerous': '1'},
            {'jkdf2_reload': '1', 'jkdf2_reload_saber': '1'},
        ],
        ids=str,
    )
    def test_generate_config_plr(
        self,
        fs: FakeFilesystem,
        generator: OpenJKDF2Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'jkdf2' / 'game')

        generator.generate(
            mock_system,
            ROMS / 'jkdf2' / 'game' / 'rom.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'jkdf2' / 'game' / 'player' / 'Batocera' / 'Batocera.plr').read_text() == snapshot(name='plr')
