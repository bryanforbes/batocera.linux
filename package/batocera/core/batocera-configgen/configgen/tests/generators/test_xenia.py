from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.generators.xenia.xeniaGenerator import XeniaGenerator
from tests.conftest import get_os_environ

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_get_version', 'wine_install_wine_trick')
class TestXeniaGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'xbox360'

    @pytest.fixture
    def emulator(self) -> str:
        return 'xenia'

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture) -> None:
        mocker.patch.dict(
            'os.environ',
            values={
                '__VK_LAYER_NV_optimus': '1',
                'FOO': 'BAR',
                '__NV_PRIME_RENDER_OFFLOAD': '1',
                '__GLX_VENDOR_LIBRARY_NAME': '1',
            },
            clear=True,
        )

    @pytest.fixture(autouse=True)
    def vulkan_is_available(self, vulkan_is_available: Mock) -> Mock:
        vulkan_is_available.return_value = True
        return vulkan_is_available

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/xenia/xenia.exe', contents='xenia.exe')
        fs.create_file('/usr/xenia/foo/bar/baz.txt')
        fs.create_file('/usr/xenia-canary/xenia_canary.exe', contents='xenia_canary.exe')
        fs.create_file('/usr/xenia-canary/ham/spam/bam.txt')
        fs.create_file('/usr/xenia-canary/patches/blah.toml')
        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert XeniaGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert XeniaGenerator().getMouseMode({}, '')

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        wine_install_wine_trick: Mock,
    ) -> None:
        assert (
            XeniaGenerator().generate(
                mock_system,
                '/userdata/roms/xbox360/rom.iso',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert wine_install_wine_trick.call_args_list == snapshot(name='winetrick')
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/portable.txt').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/portable.txt').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.config.toml').read_text() == snapshot(
            name='config'
        )
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/foo/bar/baz.txt').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/ham/spam/bam.txt').exists()
        assert not Path('/userdata/system/wine-bottles/xbox360/xenia/xenia_canary.exe').exists()
        assert not Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia.exe').exists()

    @pytest.mark.emulator('xenia-canary')
    def test_generate_canary(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        wine_install_wine_trick: Mock,
    ) -> None:
        assert (
            XeniaGenerator().generate(
                mock_system,
                '/userdata/roms/xbox360/rom.iso',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert wine_install_wine_trick.call_args_list == snapshot(name='winetrick')
        assert Path(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia-canary.config.toml'
        ).read_text() == snapshot(name='config')
        assert not Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia.exe').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe').exists()

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_config_rom(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            XeniaGenerator().generate(
                mock_system,
                'config',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_existing(
        self,
        emulator: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        shutil.copytree('/usr/xenia', '/userdata/system/wine-bottles/xbox360/xenia')
        shutil.copytree('/usr/xenia-canary', '/userdata/system/wine-bottles/xbox360/xenia-canary')

        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia/portable.txt', contents='stuff')
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia-canary/portable.txt', contents='things')

        fs.create_file(
            f'/userdata/system/wine-bottles/xbox360/{emulator}/{emulator}.config.toml',
            contents="""[CPU]
break_on_unimplemented_instructions = true

[Content]
license_mask = 0

[D3D12]
d3d12_readback_resolve = true

[Display]
fullscreen = false

[GPU]
gpu = "vulkan"

[General]
apply_patches = true

[HID]
hid = "foo"

[Logging]
log_level = 3

[Memory]
protect_zero = true

[Storage]
cache_root = "/userdata/system/cache/xenia"

[UI]
headless = true

[Vulkan]
vulkan_sparse_shared_memory = true

[XConfig]
user_language = 0
""",
        )

        XeniaGenerator().generate(
            mock_system,
            'config',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path(f'/userdata/system/wine-bottles/xbox360/{emulator}/{emulator}.config.toml').read_text() == snapshot(
            name='config'
        )
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/portable.txt').read_text() == 'stuff'
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/portable.txt').read_text() == 'things'

    def test_generate_existing_different_exe(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe', contents='xenia.exe')
        fs.create_file(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe', contents='xenia_canary.exe'
        )

        XeniaGenerator().generate(
            mock_system,
            'config',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/patches/blah.toml').exists()

    def test_generate_existing_missing_patches(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe', contents='other xenia.exe')
        fs.create_file(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe', contents='other xenia_canary.exe'
        )

        XeniaGenerator().generate(
            mock_system,
            'config',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe').read_text() == 'xenia.exe'
        assert (
            Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe').read_text()
            == 'xenia_canary.exe'
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'xenia_license': '0'},
            {'xenia_readback_resolve': 'True'},
            {'xenia_resolution': '16'},
            {'xenia_api': 'Vulkan'},
            {'xenia_api': 'foo'},
            {'xenia_vsync': 'False'},
            {'xenia_page_state': 'True'},
            {'xenia_patches': 'True'},
            {'xenia_cache': 'False'},
            {'xenia_headless': 'True'},
            {'xenia_achievement': 'True'},
            {'xenia_country': '5'},
            {'xenia_language': '2'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        XeniaGenerator().generate(
            mock_system,
            '/userdata/roms/xbox360/rom.iso',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.config.toml').read_text() == snapshot(
            name='config'
        )

    def test_generate_vulkan_unavailable(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        vulkan_is_available: Mock,
    ) -> None:
        vulkan_is_available.return_value = False

        with pytest.raises(SystemExit):
            XeniaGenerator().generate(
                mock_system,
                '/userdata/roms/xbox360/rom.iso',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )

    def test_generate_nvidia(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            XeniaGenerator().generate(
                mock_system,
                'config',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert get_os_environ() == snapshot(name='environ')
