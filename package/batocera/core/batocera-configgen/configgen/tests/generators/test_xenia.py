from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.xenia.xeniaGenerator import XeniaGenerator
from tests.conftest import get_os_environ
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import MagicMock, Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_get_version', 'wine_runner')
class TestXeniaGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[XeniaGenerator]:
        return XeniaGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'xbox360'

    @pytest.fixture
    def emulator(self) -> str:
        return 'xenia'

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture, request: SubRequest) -> None:
        key_to_add: str | None = getattr(request, 'param', None)

        mocker.patch.dict(
            'os.environ',
            values={
                'FOO': 'BAR',
                **(
                    {key_to_add: '1'}
                    if key_to_add is not None
                    else {
                        '__NV_PRIME_RENDER_OFFLOAD': '1',
                        '__VK_LAYER_NV_optimus': '1',
                        '__GLX_VENDOR_LIBRARY_NAME': '1',
                    }
                ),
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
        fs.create_file(
            '/usr/xenia-canary/patches/blah.toml',
            contents="""[[patch]]
name = 'Test Patch'
is_enabled = false
""",
        )

        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            fs.create_file(f'/usr/wine/dxvk/x64/{dll}')
            fs.create_file(f'/usr/wine/dxvk/x32/{dll}')

        fs.create_dir('/userdata/system/wine-bottles/xbox360/drive_c/windows/system32')
        fs.create_dir('/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64')

        return fs

    def test_get_mouse_mode(self, generator: XeniaGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_generate(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        wine_runner_install_wine_trick: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'xbox360' / 'rom.iso',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert wine_runner_install_wine_trick.call_args_list == snapshot(name='winetrick')
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
        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/system32/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x64/{dll}'
            )
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x32/{dll}'
            )

    @pytest.mark.emulator('xenia-canary')
    def test_generate_canary(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        wine_runner_install_wine_trick: MagicMock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'xbox360' / 'rom.iso',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert wine_runner_install_wine_trick.call_args_list == snapshot(name='winetrick')
        assert Path(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia-canary.config.toml'
        ).read_text() == snapshot(name='config')
        assert not Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia.exe').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe').exists()

        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/system32/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x64/{dll}'
            )
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x32/{dll}'
            )

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_config_rom(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('config'),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('exists', [True, False], ids=['exists', 'does not exist'])
    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_digital_title(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        exists: bool,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/xbox360/XBLA/rom.xbox360', contents='Battlezone\r\nfoo')
        if exists:
            fs.create_file('/userdata/roms/xbox360/XBLA/Battlezone')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xbox360' / 'XBLA' / 'rom.xbox360',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_existing(
        self,
        generator: XeniaGenerator,
        emulator: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            fs.create_file(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/system32/{dll}')
            fs.create_file(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64/{dll}')

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

        generator.generate(
            mock_system,
            Path('config'),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path(f'/userdata/system/wine-bottles/xbox360/{emulator}/{emulator}.config.toml').read_text() == snapshot(
            name='config'
        )
        assert Path('/userdata/system/wine-bottles/xbox360/xenia/portable.txt').read_text() == 'stuff'
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/portable.txt').read_text() == 'things'

        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/system32/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x64/{dll}'
            )
            assert Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64/{dll}').resolve() == Path(
                f'/usr/wine/dxvk/x32/{dll}'
            )

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_newer_and_partial(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        shutil.copytree('/usr/xenia-canary', '/userdata/system/wine-bottles/xbox360/xenia-canary')
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia-canary/differing.txt', contents='old contents')
        fs.create_file('/usr/xenia-canary/not-copied.txt')
        fs.create_file('/usr/xenia-canary/differing.txt', contents='new contents')

        generator.generate(
            mock_system,
            Path('config'),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/not-copied.txt').exists()
        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/differing.txt').read_text() == 'new contents'

    def test_generate_existing_missing_patches_dir(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe', contents='xenia.exe')
        fs.create_file(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe', contents='xenia_canary.exe'
        )

        generator.generate(
            mock_system,
            Path('config'),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/patches/blah.toml').exists()

    @pytest.mark.parametrize('emulator', ['xenia', 'xenia-canary'])
    def test_generate_symlink_fails(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        shutil.rmtree('/userdata/system/wine-bottles/xbox360/drive_c')

        generator.generate(
            mock_system,
            Path('config'),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        for dll in ['d3d12.dll', 'd3d12core.dll', 'd3d11.dll', 'd3d10core.dll', 'd3d9.dll', 'd3d8.dll', 'dxgi.dll']:
            assert not Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/system32/{dll}').exists()
            assert not Path(f'/userdata/system/wine-bottles/xbox360/drive_c/windows/syswow64/{dll}').exists()

    def test_generate_existing_different_exe(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file('/userdata/system/wine-bottles/xbox360/xenia/xenia.exe', contents='other xenia.exe')
        fs.create_file(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/xenia_canary.exe', contents='other xenia_canary.exe'
        )

        generator.generate(
            mock_system,
            Path('config'),
            one_player_controllers,
            {},
            [],
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
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'xbox360' / 'rom.iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.config.toml').read_text() == snapshot(
            name='config'
        )

    @pytest.mark.mock_system_config({'xenia_patches': 'True'})
    def test_generate_config_patches(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/xenia-canary/patches/12345 - some name.patch.toml',
            contents="""[[patch]]
name = 'Test Patch 1'
is_enabled = false

[[patch]]
name = 'Test Patch 2'
is_enabled = false
""",
        )

        fs.create_file(
            '/usr/xenia-canary/patches/34567 - some name 3.patch.toml',
            contents="""[[patch]]
name = 'Test Patch 3'
is_enabled = false

[[patch]]
name = 'Test Patch 4'
""",
        )
        generator.generate(
            mock_system,
            ROMS / 'xbox360' / 'some name(subtitle)[US].iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia-canary/patches/blah.toml').read_text() == snapshot(
            name='blah'
        )
        assert Path(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/patches/12345 - some name.patch.toml'
        ).read_text() == snapshot(name='patch 1')
        assert Path(
            '/userdata/system/wine-bottles/xbox360/xenia-canary/patches/34567 - some name 3.patch.toml'
        ).read_text() == snapshot(name='patch 2')

    @pytest.mark.parametrize(
        ('mock_system_config', 'vulkan_get_version'),
        [
            pytest.param({}, '1.4.0', id='new version'),
            pytest.param({}, '1.2.0', id='old version, no config'),
            pytest.param({'xenia_api': 'Vulkan'}, '1.2.0', id='old version, vulkan config'),
            pytest.param({'xenia_api': 'D3D12'}, '1.2.0', id='old version, D3D12 config'),
        ],
        indirect=['vulkan_get_version'],
    )
    def test_generate_vulkan(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'xbox360' / 'rom.iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/system/wine-bottles/xbox360/xenia/xenia.config.toml').read_text() == snapshot(
            name='config'
        )

    def test_generate_vulkan_unavailable(
        self,
        generator: XeniaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        vulkan_is_available: Mock,
    ) -> None:
        vulkan_is_available.return_value = False

        with pytest.raises(SystemExit):
            generator.generate(
                mock_system,
                ROMS / 'xbox360' / 'rom.iso',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize(
        'os_environ_nvidia',
        [
            '__NV_PRIME_RENDER_OFFLOAD',
            '__VK_LAYER_NV_optimus',
            '__GLX_VENDOR_LIBRARY_NAME',
        ],
        indirect=True,
    )
    def test_generate_nvidia(
        self,
        generator: XeniaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            generator.generate(
                mock_system,
                Path('config'),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert get_os_environ() == snapshot(name='environ')
