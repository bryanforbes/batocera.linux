from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.citra.citraGenerator import CitraGenerator

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('os_environ_lang')
class TestCitraGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return '3ds'

    @pytest.fixture
    def emulator(self) -> str:
        return 'citra'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS / 'citra-emu')

        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert CitraGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, True), ({'citra_screen_layout': '1-true'}, True), ({'citra_screen_layout': '1-false'}, False)],
        ids=str,
    )
    def test_get_mouse_mode(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert CitraGenerator().getMouseMode(mock_system_config, '') == result

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        command = CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_citra_qt(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/bin/citra-qt')

        command = CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'citra-emu' / 'qt-config.ini',
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

        CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'citra_screen_layout': '5-true'},
            {'citra_is_new_3ds': '1'},
            {'citra_is_new_3ds': '0'},
            {'citra_use_vsync_new': '1'},
            {'citra_use_vsync_new': '0'},
            {'citra_resolution_factor': '4'},
            {'citra_async_shader_compilation': '1'},
            {'citra_use_frame_limit': '0'},
            {'citra_use_disk_shader_cache': '1'},
            {'citra_custom_textures': '1-normal'},
            {'citra_custom_textures': '1-preload'},
            {'citra_graphics_api': '0'},
            {'citra_graphics_api': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_vulkan(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        vulkan_is_available: Mock,
        vulkan_has_discrete_gpu: Mock,
        vulkan_get_discrete_gpu_index: Mock,
    ) -> None:
        mock_system.config['citra_graphics_api'] = '2'
        vulkan_is_available.return_value = True
        vulkan_has_discrete_gpu.return_value = True
        vulkan_get_discrete_gpu_index.return_value = '4'

        CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

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
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_two_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad_p1: Controller,
        ps3_controller_p2: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            {
                ps3_controller_p2.player_number: ps3_controller_p2,
                generic_xbox_pad_p1.player_number: generic_xbox_pad_p1,
            },
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')

    def test_generate_no_sticks(
        self,
        mock_system: Emulator,
        gpio_controller_1_p1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = CitraGenerator().generate(
            mock_system,
            '/userdata/roms/3ds/rom.3ds',
            {
                gpio_controller_1_p1.player_number: gpio_controller_1_p1,
            },
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'citra-emu' / 'qt-config.ini').read_text() == snapshot(name='config')
