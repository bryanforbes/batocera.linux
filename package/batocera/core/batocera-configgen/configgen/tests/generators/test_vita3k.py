from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.vita3k.vita3kGenerator import Vita3kGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestVita3kGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Vita3kGenerator]:
        return Vita3kGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'psvita'

    @pytest.fixture
    def emulator(self) -> str:
        return 'vita3k'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, True), ({'vita3k_show_pointer': '1'}, True), ({'vita3k_show_pointer': '0'}, False)],
        ids=str,
    )
    def test_get_mouse_mode(  # pyright: ignore
        self, generator: Vita3kGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getMouseMode(SystemConfig(mock_system_config), Path()) == result

    def test_get_in_game_ratio(self, generator: Vita3kGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Vita3kGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'psvita' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'vita3k' / 'config.yml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: Vita3kGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'vita3k' / 'config.yml',
            contents="""
pref-path: /some/path
backend-renderer: Vulkan
resolution-multiplier: 3
enable-fxaa: 'true'
v-sync: 'false'
anisotropic-filtering: 8
enable-linear-filter: 'true'
foo: bar
""",
        )
        generator.generate(
            mock_system,
            ROMS / 'psvita' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vita3k' / 'config.yml').read_text() == snapshot

    def test_generate_existing_empty(
        self,
        generator: Vita3kGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'vita3k' / 'config.yml')

        generator.generate(
            mock_system,
            ROMS / 'psvita' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vita3k' / 'config.yml').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'vita3k_gfxbackend': 'Vulkan'},
            {'vita3k_resolution': '3'},
            {'vita3k_fxaa': '0'},
            {'vita3k_fxaa': '1'},
            {'vita3k_vsync': '0'},
            {'vita3k_vsync': '1'},
            {'vita3k_anisotropic': '8'},
            {'vita3k_linear': '0'},
            {'vita3k_linear': '1'},
            {'vita3k_surface': '0'},
            {'vita3k_surface': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Vita3kGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psvita' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vita3k' / 'config.yml').read_text() == snapshot

    def test_generate_move_saves(
        self,
        generator: Vita3kGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_dir(CONFIGS / 'vita3k' / 'ux0')
        fs.create_dir(CONFIGS / 'vita3k' / 'data')
        fs.create_dir(CONFIGS / 'vita3k' / 'lang')
        fs.create_dir(CONFIGS / 'vita3k' / 'shaders-builtin')
        fs.create_dir(CONFIGS / 'vita3k' / 'test')
        fs.create_file(CONFIGS / 'vita3k' / 'foo.txt')

        generator.generate(
            mock_system,
            ROMS / 'psvita' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert not (CONFIGS / 'vita3k' / 'ux0').exists()
        assert (CONFIGS / 'vita3k' / 'foo.txt').exists()
        assert (CONFIGS / 'vita3k' / 'data').exists()
        assert (CONFIGS / 'vita3k' / 'lang').exists()
        assert (CONFIGS / 'vita3k' / 'shaders-builtin').exists()
        assert not (CONFIGS / 'vita3k' / 'test').exists()
        assert (SAVES / 'psvita' / 'ux0').is_dir()
        assert not (SAVES / 'psvita' / 'foo.txt').exists()
        assert not (SAVES / 'psvita' / 'data').exists()
        assert not (SAVES / 'psvita' / 'lang').exists()
        assert not (SAVES / 'psvita' / 'shaders-builtin').exists()
        assert (SAVES / 'psvita' / 'test').is_dir()

    def test_generate_read_only(
        self,
        generator: Vita3kGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(SAVES / 'psvita' / 'ux0' / 'app' / 'foo')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'psvita' / 'rom name[foo].zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
