from __future__ import annotations

import filecmp
import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, DATAINIT_DIR, ROMS
from configgen.config import SystemConfig
from configgen.generators.pcsx2.pcsx2Generator import Pcsx2Generator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator
    from configgen.gun import Guns
    from configgen.types import DeviceInfoMapping, Resolution


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name')
class TestPcsx2Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Pcsx2Generator]:
        return Pcsx2Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'ps2'

    @pytest.fixture
    def emulator(self) -> str:
        return 'pcsx2'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/proc/cpuinfo', contents='\nflags  :  sse4_1 \n')
        fs.create_file(DATAINIT_DIR / 'bios' / 'ps2' / 'patches.zip', contents='patches')
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'resolution', 'result'),
        [
            ({}, {'width': 1920, 'height': 1080}, 4 / 3),
            ({'pcsx2_ratio': '16:9'}, {'width': 1920, 'height': 1080}, 16 / 9),
            ({'pcsx2_ratio': 'full'}, {'width': 1920, 'height': 1080}, 16 / 9),
            ({'pcsx2_ratio': 'full'}, {'width': 1920, 'height': 1145}, 4 / 3),
            ({'pcsx2_ratio': '4:3'}, {'width': 1920, 'height': 1080}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: Pcsx2Generator, mock_system_config: dict[str, Any], resolution: Resolution, result: bool
    ) -> None:
        assert (
            generator.getInGameRatio(SystemConfig(mock_system_config), resolution, ROMS / 'ps2' / 'rom.chd') == result
        )

    def test_generate(
        self,
        generator: Pcsx2Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps2' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'PCSX2' / 'game_controller_db.txt').read_text() == snapshot(name='controllerdb')
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')
        assert (CONFIGS / 'PCSX2' / 'PCSX2-reg.ini').read_text() == snapshot(name='reg')
        assert (CONFIGS / 'PCSX2' / 'inis' / 'spu2-x.ini').read_text() == snapshot(name='audio')
        assert filecmp.cmp(DATAINIT_DIR / 'bios' / 'ps2' / 'patches.zip', BIOS / 'ps2' / 'patches.zip')

    def test_generate_existing(
        self,
        generator: Pcsx2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'PCSX2' / 'inis' / 'PCSX2_ui.ini')
        fs.create_file(CONFIGS / 'PCSX2' / 'inis' / 'PCSX2_vm.ini')
        fs.create_file(CONFIGS / 'PCSX2' / 'inis' / 'GS.ini')
        fs.create_file(BIOS / 'ps2' / 'patches.zip', contents='new patches')
        fs.create_file(
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SCES-52530'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png'
        )
        fs.create_file(
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SLUS-20927'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png'
        )
        fs.create_file(CONFIGS / 'PCSX2' / 'inis' / 'spu2-x.ini', contents='existing audio')
        fs.create_file(
            CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini',
            contents="""[UI]
SettingsVersion = 2

[Folders]
Bios = ../../../bios/ps2

[EmuCore]
EnableDiscordPresence = true

[Achievements]
Enabled = true

[Filenames]

[EmuCore/GS]
Renderer = 18

[InputSources]
Keyboard = false

[Hotkeys]
ToggleFullscreen = 1

[Pad]
MultitapPort1 = true

[Pad1]
Type = blah

[GameList]
RecursivePaths = /foo

[Spam]
ham = bam

[USB1]
Type = guncon2
guncon2_Start = 1
guncon2_C = 1
guncon2_numdevice = 1

[USB2]
Type = guncon2
guncon2_Start = 1
guncon2_C = 1
guncon2_numdevice = 1
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert not (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2_ui.ini').exists()
        assert not (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2_vm.ini').exists()
        assert not (CONFIGS / 'PCSX2' / 'inis' / 'GS.ini').exists()
        assert not (
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SCES-52530'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png'
        ).exists()
        assert not (
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SLUS-20927'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png'
        ).exists()
        assert (BIOS / 'ps2' / 'patches.zip').read_text() == 'new patches'
        assert (CONFIGS / 'PCSX2' / 'inis' / 'spu2-x.ini').read_text() == 'existing audio'
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')

    def test_generate_config_rom(
        self,
        generator: Pcsx2Generator,
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
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'state_filename': 'state-filename-1'},
            {'state_slot': 'state-slot-1'},
            {'pcsx2_fastboot': '0'},
            {'pcsx2_fastboot': '1'},
            {'pcsx2_cheats': 'true'},
            {'pcsx2_cheats': 'false'},
            {'pcsx2_EnableWideScreenPatches': 'true'},
            {'pcsx2_EnableWideScreenPatches': 'false'},
            {'pcsx2_interlacing_patches': 'true'},
            {'pcsx2_interlacing_patches': 'false'},
            {'pcsx2_ratio': 'Stretch'},
            {'pcsx2_ratio': '4:3'},
            {'pcsx2_ratio': '16:9'},
            {'pcsx2_vsync': '0'},
            {'pcsx2_vsync': '1'},
            {'pcsx2_resolution': '1.25'},
            {'pcsx2_resolution': '4'},
            {'pcsx2_fxaa': 'true'},
            {'pcsx2_fxaa': 'false'},
            {'pcsx2_fmv_ratio': 'off'},
            {'pcsx2_fmv_ratio': '4:3'},
            {'pcsx2_fmv_ratio': '16:9'},
            {'pcsx2_mipmapping': '0'},
            {'pcsx2_mipmapping': '1'},
            {'pcsx2_mipmapping': '2'},
            {'pcsx2_trilinear_filtering': '0'},
            {'pcsx2_trilinear_filtering': '1'},
            {'pcsx2_trilinear_filtering': '2'},
            {'pcsx2_anisotropic_filtering': '2'},
            {'pcsx2_anisotropic_filtering': '4'},
            {'pcsx2_dithering': '1'},
            {'pcsx2_dithering': '2'},
            {'pcsx2_texture_loading': '0'},
            {'pcsx2_texture_loading': '1'},
            {'pcsx2_deinterlacing': '1'},
            {'pcsx2_deinterlacing': '2'},
            {'pcsx2_blur': 'true'},
            {'pcsx2_blur': 'false'},
            {'pcsx2_scaling': 'true'},
            {'pcsx2_scaling': 'false'},
            {'pcsx2_blending': '0'},
            {'pcsx2_blending': '2'},
            {'pcsx2_texture_filtering': '0'},
            {'pcsx2_texture_filtering': '2'},
            {'pcsx2_bilinear_filtering': '0'},
            {'pcsx2_bilinear_filtering': '2'},
            {'pcsx2_texture_replacements': 'true'},
            {'pcsx2_texture_replacements': 'false'},
            {'pcsx2_osd_messages': 'true'},
            {'pcsx2_osd_messages': 'false'},
            {'pcsx2_shaderset': '1'},
            {'pcsx2_shaderset': '2'},
            {'autosave': '0'},
            {'autosave': '1'},
            {'incrementalsavestates': '0'},
            {'incrementalsavestates': '1'},
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.token': 'token',
            },
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.token': 'token',
                'retroachievements.hardcore': '1',
                'retroachievements.challenge_indicators': '1',
                'retroachievements.richpresence': '1',
                'retroachievements.leaderboards': '1',
                'retroachievements.encore': '1',
                'retroachievements.unofficial': '1',
            },
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Pcsx2Generator,
        mocker: MockerFixture,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        mocker.patch('time.time', return_value=1.1)

        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps2' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')

    @pytest.mark.mock_system_config({'pcsx2_crisis_fog': 'true'})
    def test_generate_config_crisis_fog(
        self,
        generator: Pcsx2Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            Path('/usr/pcsx2/bin/resources')
            / 'textures'
            / 'SCES-52530'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
            contents='sces-52530',
        )
        fs.create_file(
            Path('/usr/pcsx2/bin/resources')
            / 'textures'
            / 'SLUS-20927'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
            contents='slus-20927',
        )
        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')
        assert filecmp.cmp(
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SCES-52530'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
            Path('/usr/pcsx2/bin/resources')
            / 'textures'
            / 'SCES-52530'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
        )
        assert filecmp.cmp(
            CONFIGS
            / 'PCSX2'
            / 'textures'
            / 'SLUS-20927'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
            Path('/usr/pcsx2/bin/resources')
            / 'textures'
            / 'SLUS-20927'
            / 'replacements'
            / 'c321d53987f3986d-eadd4df7c9d76527-00005dd4.png',
        )

    @pytest.mark.parametrize(
        ('vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name', 'mock_system_config'),
        [
            (False, None, {}),
            (False, 'discrete name', {}),
            (False, None, {'pcsx2_gfxbackend': '12'}),
            (False, None, {'pcsx2_gfxbackend': '13'}),
            (False, None, {'pcsx2_gfxbackend': '14'}),
            (True, None, {'pcsx2_gfxbackend': '14'}),
            (True, 'discrete name', {'pcsx2_gfxbackend': '14'}),
        ],
        indirect=['vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name'],
    )
    def test_generate_vulkan(
        self,
        generator: Pcsx2Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        vulkan_is_available: Mock,
    ) -> None:
        vulkan_is_available.return_value = True
        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')

    @pytest.mark.mock_system_config({'use_guns': '1'})
    @pytest.mark.parametrize(
        ('mock_system_config', 'metadata', 'guns'),
        [
            pytest.param({}, {}, [], id='no guns'),
            pytest.param({}, {}, [{}], id='1 Gun'),
            pytest.param({'controllers.pedals1': 'z'}, {}, [{}], id='1 Gun, with pedal'),
            pytest.param({}, {}, [{}, {}], id='2 Guns'),
            pytest.param(
                {'controllers.pedals2': 'u', 'pcsx2_crosshairs': '1'},
                {},
                [{}, {}],
                id='2 Guns, with gun 2 pedal and crosshairs',
            ),
            pytest.param({}, {'gun_gun1port': '2'}, [{}], id='1 Gun, Gun 1 on port 2'),
        ],
    )
    def test_generate_guns(
        self,
        generator: Pcsx2Generator,
        mock_system: Emulator,
        metadata: dict[str, Any],
        guns: Guns,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            two_player_controllers,
            metadata,
            guns,
            {},
            {},  # pyright: ignore
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')

    @pytest.mark.mock_system_config({'use_wheels': '1'})
    @pytest.mark.parametrize(
        ('mock_system_config', 'metadata', 'wheels'),
        [
            pytest.param({}, {}, {}, id='no wheels'),
            pytest.param({}, {}, {'/dev/input/event1': {}}, id='1 virtual wheel'),
            pytest.param({}, {'wheel_type': 'DrivingForce'}, {'/dev/input/event1': {}}, id='1 driving force wheel'),
            pytest.param(
                {'pcsx2_wheel_type': 'DrivingForcePro'},
                {'wheel_type': 'DrivingForce'},
                {'/dev/input/event1': {}},
                id='1 driving force pro wheel',
            ),
            pytest.param(
                {'pcsx2_wheel_type': 'DrivingForcePro'},
                {'wheel_type': 'DrivingForce'},
                {'/dev/input/event1': {}, '/dev/input/event2': {}},
                id='2 driving force pro wheels',
            ),
        ],
    )
    def test_generate_wheels(
        self,
        generator: Pcsx2Generator,
        mock_system: Emulator,
        metadata: dict[str, Any],
        wheels: DeviceInfoMapping,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            make_player_controller_list(generic_xbox_pad, ps3_controller),
            metadata,
            [],
            wheels,
            {},  # pyright: ignore
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')

    @pytest.mark.parametrize(
        ('mock_system_config', 'num_controllers'),
        [
            pytest.param({'pcsx2_multitap': '4'}, 2, id='multitap 4, 2 controllers'),
            pytest.param({'pcsx2_multitap': '4'}, 3, id='multitap 4, 3 controllers'),
            pytest.param({'pcsx2_multitap': '4'}, 5, id='multitap 4, 5 controllers'),
            pytest.param({'pcsx2_multitap': '8'}, 2, id='multitap 8, 2 controllers'),
            pytest.param({'pcsx2_multitap': '8'}, 3, id='multitap 8, 3 controllers'),
            pytest.param({'pcsx2_multitap': '8'}, 5, id='multitap 8, 5 controllers'),
        ],
    )
    def test_generate_multitap(
        self,
        generator: Pcsx2Generator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        num_controllers: int,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'ps2' / 'rom.chd',
            make_player_controller_list(*itertools.repeat(generic_xbox_pad, num_controllers)),
            {},
            [],
            {},
            {},  # pyright: ignore
        )
        assert (CONFIGS / 'PCSX2' / 'inis' / 'PCSX2.ini').read_text() == snapshot(name='ini')
