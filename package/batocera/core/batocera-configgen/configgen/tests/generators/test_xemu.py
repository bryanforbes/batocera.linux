from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.xemu.xemuGenerator import XemuGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


class TestXemuGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[XemuGenerator]:
        return XemuGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'xbox'

    @pytest.fixture
    def emulator(self) -> str:
        return 'xemu'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/share/xemu/data/xbox_hdd.qcow2', contents='xbox_hdd.qcow2')
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'xemu_scaling': 'scale'}, 4 / 3),
            ({'xemu_aspect': 'native'}, 4 / 3),
            ({'xemu_scaling': 'stretch'}, 16 / 9),
            ({'xemu_aspect': '16x9'}, 16 / 9),
            ({'xemu_scaling': 'scale', 'xemu_aspect': '16x9'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: XemuGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: XemuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'xbox' / 'rom.iso',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert filecmp.cmp('/usr/share/xemu/data/xbox_hdd.qcow2', SAVES / 'xbox' / 'xbox_hdd.qcow2')
        assert (CONFIGS / 'xemu' / 'xemu.toml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: XemuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(SAVES / 'xbox' / 'xbox_hdd.qcow2', contents='saved xbox_hdd.qcow2')
        fs.create_file(
            CONFIGS / 'xemu' / 'xemu.toml',
            contents="""[general]
skip_boot_anim = true

[sys]
mem_limit = "128"

[sys.files]
flashrom_path = "/tmp/Complex_4627.bin"

[audio]
use_dsp = true

[display]
renderer = "VULKAN"

[display.quality]
surface_scale = 2

[display.window]
fullscreen_on_startup = false

[display.ui]
show_menubar = true

[input.bindings]
port1 = "foobarbaz"

[net]
enable = true

[net.udp]
remote_addr = "10.10.10.10"
bind_addr = "10.10.10.10"
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'xbox' / 'rom.iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'xbox' / 'xbox_hdd.qcow2').read_text() == 'saved xbox_hdd.qcow2'
        assert (CONFIGS / 'xemu' / 'xemu.toml').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'xemu_bootanim': 'true'},
            {'xemu_memory': '128'},
            {'xemu_use_dsp': 'true'},
            {'xemu_api': 'OPENGL'},
            {'xemu_render': '2'},
            {'xemu_vsync': 'false'},
            {'xemu_scaling': 'stretch'},
            {'xemu_aspect': '16x9'},
            {'xemu_networktype': 'nat'},
            {'xemu_udpremote': '10.10.10.10'},
            {'xemu_udpbind': '10.10.10.10'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: XemuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'xbox' / 'rom.iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'xemu' / 'xemu.toml').read_text() == snapshot

    @pytest.mark.system_name('chihiro')
    def test_generate_chihiro(
        self,
        generator: XemuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'chihiro' / 'rom.iso',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'xemu' / 'xemu.toml').read_text() == snapshot

    def test_generate_controllers(
        self,
        generator: XemuGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'xbox' / 'rom.iso',
            make_player_controller_list(
                generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad
            ),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'xemu' / 'xemu.toml').read_text() == snapshot
