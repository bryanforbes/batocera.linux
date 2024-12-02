from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.rpcs3.rpcs3Generator import Rpcs3Generator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name')
class TestRpcs3Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Rpcs3Generator]:
        return Rpcs3Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'ps3'

    @pytest.fixture
    def emulator(self) -> str:
        return 'rpcs3'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/share/rpcs3/Icons/test_icon')
        return fs

    def test_get_in_game_ratio(self, generator: Rpcs3Generator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 1, 'height': 1}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Rpcs3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps3' / 'rom_dir',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'rpcs3' / 'config.yml').read_text() == snapshot(name='config')
        assert (CONFIGS / 'rpcs3' / 'GuiConfigs' / 'CurrentSettings.ini').read_text() == snapshot(
            name='currentsettings'
        )
        assert (CONFIGS / 'rpcs3' / 'input_configs' / 'global' / 'Default.yml').read_text() == snapshot(name='input')
        assert (CONFIGS / 'rpcs3' / 'Icons' / 'test_icon').exists()

    def test_generate_configure_emulator(
        self,
        generator: Rpcs3Generator,
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

    def test_generate_existing(
        self,
        generator: Rpcs3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'rpcs3' / 'GuiConfigs' / 'CurrentSettings.ini',
            contents="""[main_window]
confirmationBoxExitGame = true
""",
        )
        fs.create_file(
            CONFIGS / 'rpcs3' / 'config.yml',
            contents="""Audio: {}
Core: {}
Input/Output: {}
Log: {}
Miscellaneous: {}
Net: {}
Savestate: {}
System: {}
VFS: {}
Video: {}
Foo: {}
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'ps3' / 'rom_dir',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'rpcs3' / 'config.yml').read_text() == snapshot(name='config')
        assert (CONFIGS / 'rpcs3' / 'GuiConfigs' / 'CurrentSettings.ini').read_text() == snapshot(
            name='currentsettings'
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'use_guns': '1'},
            {'rpcs3_ppudecoder': 'Interpreter (dynamic)'},
            {'rpcs3_spudecoder': 'Recompiler (ASMJIT)'},
            {'rpcs3_spuxfloataccuracy': 'accurate'},
            {'rpcs3_spuxfloataccuracy': 'relaxed'},
            {'rpcs3_spuxfloataccuracy': 'approximate'},
            {'rpcs3_sputhreads': '2'},
            {'rpcs3_spuloopdetection': 'True'},
            {'rpcs3_spublocksize': 'Mega'},
            {'rpcs3_maxcpu_preemptcount': '50'},
            {'rpcs3_shadermode': 'Async with Shader Interpreter'},
            {'rpcs3_vsync': 'True'},
            {'rpcs3_stretchdisplay': 'True'},
            {'rpcs3_framelimit': 'Off'},
            {'rpcs3_framelimit': '30'},
            {'rpcs3_framelimit': '50'},
            {'rpcs3_framelimit': '59.94'},
            {'rpcs3_framelimit': '60'},
            {'rpcs3_framelimit': '20'},
            {'rpcs3_colorbuffers': 'True'},
            {'rpcs3_vertexcache': 'True'},
            {'rpcs3_anisotropic': '4'},
            {'rpcs3_aa': 'Disabled'},
            {'rpcs3_zcull': 'Approximate'},
            {'rpcs3_zcull': 'Relaxed'},
            {'rpcs3_shader': 'Ultra'},
            {'rpcs3_resolution_scale': '200'},
            {'rpcs3_scaling': 'Nearest'},
            {'rpcs3_num_compilers': '1'},
            {'rpcs3_rsx': 'True'},
            {'rpcs3_async_texture': 'True'},
            {'rpcs3_audio_format': 'Stereo'},
            {'rpcs3_audio_16bit': 'True'},
            {'rpcs3_audio_16bit': 'False'},
            {'rpcs3_audiobuffer': 'False'},
            {'rpcs3_audiobuffer_duration': '10'},
            {'rpcs3_timestretch': 'True'},
            {'rpcs3_timestretch_threshold': '15'},
            {'rpcs3_crosshairs': 'True'},
            {'rpcs3_gui': 'False'},
            {'rpcs3_gui': 'True'},
            {'rpcs3_sleep_timers_accuracy': 'As Host'},
            {'rpcs3_sleep_timers_accuracy': 'Usleep Only'},
            {'rpcs3_sleep_timers_accuracy': 'All Timers'},
            {'rpcs3_write_depth_buffers': 'False'},
            {'rpcs3_write_depth_buffers': 'True'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mocker: MockerFixture,
        generator: Rpcs3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps3' / 'rom_dir',
                one_player_controllers,
                {},
                [mocker.Mock()],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'rpcs3' / 'config.yml').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        ('vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name', 'mock_system_config'),
        [
            (False, None, {'rpcs3_gfxbackend': 'OpenGL'}),
            (False, None, {}),
            (True, None, {}),
            (True, 'discrete name', {}),
        ],
        indirect=['vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name'],
    )
    def test_generate_vulkan(
        self,
        generator: Rpcs3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        vulkan_is_available: Mock,
    ) -> None:
        vulkan_is_available.return_value = True
        generator.generate(
            mock_system,
            ROMS / 'ps3' / 'rom_dir',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'rpcs3' / 'config.yml').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        ('mock_system_config', 'resolution'),
        [
            ({'rpcs3_ratio': '4:3'}, {}),
            ({}, {'width': 1920, 'height': 1201}),
        ],
    )
    def test_generate_ratio(
        self,
        generator: Rpcs3Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        resolution: Resolution,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'ps3' / 'rom_dir',
            one_player_controllers,
            {},
            [],
            {},
            resolution,
        )
        assert (CONFIGS / 'rpcs3' / 'config.yml').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        ('contents', 'update_exists'),
        [
            ('\nrelease:400:800\n', False),
            ('\nfoo:bar:baz\nspam:ham:bam\n', False),
            ('\nrelease:400:800\n', True),
            ('\nfoo:bar:baz\nspam:ham:bam\n', True),
        ],
    )
    def test_generate_firmware(
        self,
        generator: Rpcs3Generator,
        fs: FakeFilesystem,
        contents: str,
        update_exists: bool,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'rpcs3' / 'dev_flash' / 'vsh' / 'etc' / 'version.txt', contents=contents)
        if update_exists:
            fs.create_file(BIOS / 'PS3UPDAT.PUP')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps3' / 'rom_dir',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_psn_rom(
        self,
        generator: Rpcs3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'ps3' / 'rom.psn', contents='123456789')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps3' / 'rom.psn',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_psn_rom_raises(
        self,
        generator: Rpcs3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(ROMS / 'ps3' / 'rom.psn', contents='12345678')

        with pytest.raises(BatoceraException, match=r'^No game ID found in \/'):
            generator.generate(
                mock_system,
                ROMS / 'ps3' / 'rom.psn',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.mock_system_config(
        {
            'rpcs3_rumble2': '0',
            'rpcs3_controller3': 'Evdev',
            'rpcs3_controller4': 'Evdev',
            'rpcs3_rumble4': '0',
            'rpcs3_controller5': 'Sony',
            'rpcs3_controller6': 'Sony',
            'rpcs3_controller7': 'Sony',
            'rpcs3_rumble7': '0',
        }
    )
    def test_generate_controllers(
        self,
        generator: Rpcs3Generator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        ds4_controller: Controller,
        ds5_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(
            generic_xbox_pad,
            generic_xbox_pad,
            generic_xbox_pad,
            generic_xbox_pad,
            ps3_controller,
            ds4_controller,
            ds5_controller,
            generic_xbox_pad,
        )
        generator.generate(
            mock_system,
            ROMS / 'ps3' / 'rom_dir',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'rpcs3' / 'input_configs' / 'global' / 'Default.yml').read_text() == snapshot(name='input')
