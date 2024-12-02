from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.config import SystemConfig
from configgen.generators.azahar.azaharGenerator import AzaharGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('os_environ_lang')
class TestAzaharGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[AzaharGenerator]:
        return AzaharGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return '3ds'

    @pytest.fixture
    def emulator(self) -> str:
        return 'azahar'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS / 'azaharplus-emu')

        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, True), ({'azahar_screen_layout': '1-true'}, True), ({'azahar_screen_layout': '1-false'}, False)],
        ids=str,
    )
    def test_get_mouse_mode(  # pyright: ignore
        self, generator: AzaharGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getMouseMode(SystemConfig(mock_system_config), Path()) == result

    def test_generate(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('/userdata/roms/3ds/rom.3ds'),
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: AzaharGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'azaharplus-emu' / 'qt-config.ini',
            contents=r"""[Layout]
custom_layout = true

[System]
is_new_3ds = true

[UI]
fullscreen = false

[Renderer]
use_hw_renderer = false

[WebService]
enable_telemetry = true

[Utility]
use_disk_shader_cache = true

[Controls]
profile = 0
profile\default = false
profiles\1\name = default
profiles\1\name\default = true
profiles\size = 1
""",
        )

        generator.generate(
            mock_system,
            Path('/userdata/roms/3ds/rom.3ds'),
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'azahar_screen_layout': '5-true'},
            {'azahar_is_new_3ds': '1'},
            {'azahar_is_new_3ds': '0'},
            {'azahar_use_vsync_new': '1'},
            {'azahar_use_vsync_new': '0'},
            {'azahar_resolution_factor': '4'},
            {'azahar_async_shader_compilation': '1'},
            {'azahar_use_frame_limit': '0'},
            {'azahar_use_disk_shader_cache': '1'},
            {'azahar_custom_textures': '1-normal'},
            {'azahar_custom_textures': '1-preload'},
            {'azahar_graphics_api': '0'},
            {'azahar_graphics_api': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            Path('/userdata/roms/3ds/rom.3ds'),
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_vulkan(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        vulkan_is_available: Mock,
        vulkan_has_discrete_gpu: Mock,
        vulkan_get_discrete_gpu_index: Mock,
    ) -> None:
        mock_system.config['azahar_graphics_api'] = '2'
        vulkan_is_available.return_value = True
        vulkan_has_discrete_gpu.return_value = True
        vulkan_get_discrete_gpu_index.return_value = '4'

        generator.generate(
            mock_system,
            Path('/userdata/roms/3ds/rom.3ds'),
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            'ja_JP',
            'en_US',
            'de_DE',
            'es_ES',
            'fr_FR',
            'it_IT',
            'hu_HU',
            'pt_PT',
            'ru_RU',
            'en_AU',
            'zh_CN',
            'ko_KR',
            'zh_TW',
            'en_GB',
        ],
        indirect=True,
    )
    def test_generate_lang(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            Path('/userdata/roms/3ds/rom.3ds'),
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_two_controllers(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('/userdata/roms/3ds/rom.3ds'),
                make_player_controller_list(generic_xbox_pad, ps3_controller),
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_no_sticks(
        self,
        generator: AzaharGenerator,
        mock_system: Emulator,
        gpio_controller_1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('/userdata/roms/3ds/rom.3ds'),
                make_player_controller_list(gpio_controller_1),
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'azaharplus-emu' / 'qt-config.ini').read_text() == snapshot(name='config')
