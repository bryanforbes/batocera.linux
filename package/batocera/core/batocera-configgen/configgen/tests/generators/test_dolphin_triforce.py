from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.dolphin_triforce.dolphinTriforceGenerator import DolphinTriforceGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


_INI_FILES: Final = list((Path(__file__).parents[5] / 'emulators' / 'dolphin-triforce').glob('*.ini'))


@pytest.mark.usefixtures('os_environ_lang')
class TestDolphinTriforceGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DolphinTriforceGenerator]:
        return DolphinTriforceGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'triforce'

    @pytest.fixture
    def emulator(self) -> str:
        return 'dolphin_triforce'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        for file in _INI_FILES:
            fs.add_real_file(file, target_path=Path('/usr/share/triforce') / file.name)
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'resolution', 'result'),
        [
            ({}, {'width': 1920, 'height': 1080}, 4 / 3),
            ({'triforce_aspect_ratio': '3'}, {'width': 1920, 'height': 1145}, 4 / 3),
            ({'triforce_aspect_ratio': '1'}, {'width': 1920, 'height': 1145}, 16 / 9),
            ({'triforce_aspect_ratio': '3'}, {'width': 1920, 'height': 1144}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self,
        generator: DolphinTriforceGenerator,
        mock_system_config: dict[str, Any],
        resolution: Resolution,
        result: bool,
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), resolution, Path()) == result

    def test_generate(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'triforce' / 'rom.gcm',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot(name='gcpadnew')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GFX.ini').read_text() == snapshot(name='gfx')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Logger.ini').read_text() == snapshot(name='logger')
        for file in _INI_FILES:
            assert filecmp.cmp(
                CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name, Path('/usr/share/triforce') / file.name
            )

    def test_generate_existing(
        self,
        generator: DolphinTriforceGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'dolphin-triforce' / 'Config' / 'Dolphin.ini',
            contents="""[General]
ISOPath0 = /path/to/triforce
ISOPaths = 1
GCMPath0 = /path/to/triforce
GCMPathes = 1

[Core]
EnableCheats = False

[Interface]
UsePanicHandlers = True

[Analytics]
PermissionAsked = False

[Display]
RenderToMain = True

[Foo]
Bar = 1
""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini',
            contents="""[Hotkeys1]
Device = SDL/0/real name 8

[Foo]
Bar = 1
""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-triforce' / 'Config' / 'GFX.ini',
            contents="""[Settings]
AspectRatio = 1

[Hacks]

[Enhancements]
MaxAnisotropy = 1

[Hardware]
VSync = False

[Foo]
Bar = 1
""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-triforce' / 'Config' / 'Logger.ini',
            contents="""[Logs]
DVD = True

[Foo]
Bar = 1
""",
        )
        for file in _INI_FILES:
            fs.create_file(CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name, contents='newer config')

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GFX.ini').read_text() == snapshot(name='gfx')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Logger.ini').read_text() == snapshot(name='logger')
        for file in _INI_FILES:
            assert (CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name).read_text() == 'newer config'

    def test_generate_existing_older(
        self,
        generator: DolphinTriforceGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        for file in _INI_FILES:
            fs.create_file(CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name, contents='newer config')
            fs.utime(str(CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name), times=(0, 0))

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        for file in _INI_FILES:
            assert filecmp.cmp(
                CONFIGS / 'dolphin-triforce' / 'GameSettings' / file.name, Path('/usr/share/triforce') / file.name
            )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'showFPS': True},
            {'triforce_osd_messages': '0'},
            {'triforce_osd_messages': '1'},
            {'triforce_dual_core': '0'},
            {'triforce_dual_core': '1'},
            {'triforce_gpu_sync': '0'},
            {'triforce_gpu_sync': '1'},
            {'triforce_enable_mmu': '0'},
            {'triforce_enable_mmu': '1'},
            {'triforce_api': 'Vulkan'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Dolphin.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'triforce_aspect_ratio': '1'},
            {'triforce_hires_textures': '0'},
            {'triforce_hires_textures': '1'},
            {'widescreen_hack': '0'},
            {'widescreen_hack': '1'},
            {'widescreen_hack': '1', 'enable_cheats': '0'},
            {'widescreen_hack': '1', 'enable_cheats': '1'},
            {'triforce_perf_hacks': '0'},
            {'triforce_perf_hacks': '1'},
            {'triforce_resolution': '3'},
            {'triforce_vsync': '0'},
            {'triforce_vsync': '1'},
            {'triforce_filtering': '1/2'},
            {'triforce_resampling': '1'},
            {'triforce_antialiasing': '0x00000010/False'},
        ],
        ids=str,
    )
    def test_generate_gfx_config(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GFX.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            'en_US',
            'de_DE',
            'fr_FR',
            'es_ES',
            'it_IT',
            'nl_NL',
            'pt_BR',
        ],
        indirect=True,
    )
    def test_generate_lang(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Dolphin.ini').read_text() == snapshot

    def test_generate_controllers(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(generic_xbox_pad, generic_xbox_pad, ps3_controller)

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot(name='gcpadnew')

    @pytest.mark.mock_system_config({'triforce_rumble': 'Triangle'})
    def test_generate_controllers_rumble(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(generic_xbox_pad, generic_xbox_pad, ps3_controller)

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'rom.gcm',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot

    def test_generate_controllers_virtua_striker(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(generic_xbox_pad, generic_xbox_pad, ps3_controller)

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'virtua.gcm',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot(name='gcpadnew')

    def test_generate_controllers_keyboard(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(keyboard_controller)

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'virtua.gcm',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot(name='gcpadnew')

    def test_generate_controllers_hotkey_not_button(
        self,
        generator: DolphinTriforceGenerator,
        mock_system: Emulator,
        gpio_controller_2: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(gpio_controller_2)

        generator.generate(
            mock_system,
            ROMS / 'triforce' / 'virtua.gcm',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-triforce' / 'Config' / 'GCPadNew.ini').read_text() == snapshot(name='gcpadnew')
