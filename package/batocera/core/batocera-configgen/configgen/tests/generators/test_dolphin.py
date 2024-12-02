from __future__ import annotations

from pathlib import Path
from struct import pack
from typing import TYPE_CHECKING, Any, cast

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.dolphin.dolphinGenerator import DolphinGenerator
from configgen.gun import Gun
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator
    from configgen.types import DeviceInfo, Resolution


def _sysconf(*items: tuple[str, int, bytes]) -> bytes:
    # Generates the contents of SYSCONF according to the information found at
    # https://wiibrew.org/wiki//shared2/sys/SYSCONF
    num_items = len(items)

    sysconf_header = b'SCv0' + pack('>H', num_items)
    sysconf_items = b''

    offset = 6 + ((num_items + 1) * 2)

    for item in items:
        sysconf_header += pack('>H', offset)
        item_data = pack('B', (item[1] << 5) | (len(item[0]) - 1)) + item[0].encode('utf-8') + item[2]
        offset += len(item_data)
        sysconf_items += item_data

    sysconf_header += pack('>H', offset)

    return sysconf_header + sysconf_items + b'\x00' * (16380 - len(sysconf_header)) + b'SCed'


def _big_array(name: str, data: bytes) -> tuple[str, int, bytes]:
    return (name, 1, pack('>H', len(data) - 1) + data)


def _small_array(name: str, data: bytes) -> tuple[str, int, bytes]:
    return (name, 2, pack('B', len(data) - 1) + data)


def _byte(name: str, data: int) -> tuple[str, int, bytes]:
    return (name, 3, pack('B', data))


def _short(name: str, data: int) -> tuple[str, int, bytes]:
    return (name, 4, pack('>H', data))


def _long(name: str, data: int) -> tuple[str, int, bytes]:
    return (name, 5, pack('>L', data))


def _long_long(name: str, data: int) -> tuple[str, int, bytes]:
    return (name, 6, pack('>Q', data))


def _bool(name: str, data: bool) -> tuple[str, int, bytes]:
    return (name, 7, pack('B', 1 if data else 0))


@pytest.mark.usefixtures(
    'os_environ_lang', 'vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index'
)
class TestDolphinGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return DolphinGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'gamecube'

    @pytest.fixture
    def emulator(self) -> str:
        return 'dolphin'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/dolphin-emu')
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'gfx_aspect_ratio', 'resolution', 'result'),
        [
            pytest.param({}, '0', {'width': 0, 'height': 0}, 4 / 3, id='auto, default settings'),
            pytest.param({'tv_mode': '0'}, '0', {'width': 0, 'height': 0}, 4 / 3, id='auto, 4/3 tv_mode'),
            pytest.param({'tv_mode': '1'}, '0', {'width': 0, 'height': 0}, 16 / 9, id='auto, 16/9 tv_mode'),
            pytest.param({'tv_mode': '0'}, '1', {'width': 0, 'height': 0}, 16 / 9, id='forced 16/9, 4/3 tv_mode'),
            pytest.param({'tv_mode': '1'}, '1', {'width': 0, 'height': 0}, 16 / 9, id='forced 16/9, 16/9 tv_mode'),
            pytest.param({'tv_mode': '0'}, '2', {'width': 0, 'height': 0}, 4 / 3, id='forced 4/3, 4/3 tv_mode'),
            pytest.param({'tv_mode': '1'}, '2', {'width': 0, 'height': 0}, 4 / 3, id='forced 4/3, 16/9 tv_mode'),
            pytest.param({'tv_mode': '0'}, '3', {'width': 1920, 'height': 1080}, 16 / 9, id='stretched, 4/3 tv_mode'),
            pytest.param({'tv_mode': '1'}, '3', {'width': 640, 'height': 480}, 4 / 3, id='stretched, 16/9 tv_mode'),
            pytest.param({'tv_mode': '1'}, '4', {'width': 640, 'height': 480}, 4 / 3, id='unknown aspect ratio'),
        ],
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self,
        generator: Generator,
        fs: FakeFilesystem,
        gfx_aspect_ratio: str,
        resolution: Resolution,
        mock_system_config: dict[str, Any],
        result: bool,
    ) -> None:
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'GFX.ini',
            contents=f"""[Settings]
AspectRatio = {gfx_aspect_ratio}
""",
        )

        assert generator.getInGameRatio(SystemConfig(mock_system_config), resolution, Path()) == result

    def test_generate(self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'gamecube' / 'rom.gcz',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dolphin-emu' / 'Qt.ini').read_text() == snapshot(name='qt')
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')
        assert (CONFIGS / 'dolphin-emu' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-emu' / 'RetroAchievements.ini').read_text() == snapshot(name='ra')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')

    @pytest.mark.system_name('foo')
    def test_generate_raises(self, generator: Generator, mock_system: Emulator) -> None:
        with pytest.raises(BatoceraException, match=r"^Invalid system name: 'foo'$"):
            generator.generate(
                mock_system,
                ROMS / 'gamecube' / 'rom.gcz',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    def test_generate_nogui(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.remove('/usr/bin/dolphin-emu')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'gamecube' / 'rom.gcz',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'Qt.ini',
            contents="""[Emulation]
StateSlot = 2
Foo = 3

[Bar]
Baz = 1
""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'Dolphin.ini',
            contents="""[General]
ISOPath0 = /path/to/roms/wii
ISOPath1 = /path/to/roms/gamecube
ISOPaths = 3

[Core]
EnableCheats = True
Foo = 1

[DSP]
EnableJIT = True

[Interface]
UsePanicHandlers = True

[Analytics]
PermissionAsked = False

[Display]

[GBA]

[Bar]
Baz = 1
""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'GFX.ini',
            contents="""[Settings]
ShowFPS = True
Foo = 1

[Hacks]
VISkip = True

[Enhancements]
MaxAnisotropy = 1

[Hardware]
VSync = False

[Bar]
Baz = 1
""",
        )
        fs.create_file(CONFIGS / 'dolphin-emu' / 'Hotkeys.ini', contents="""old hotkeys config""")
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'RetroAchievements.ini',
            contents="""old ra config""",
        )
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'GCPadNew.ini', encoding='utf_8_sig', contents="""old controller config"""
        )

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'dolphin-emu' / 'Qt.ini').read_text() == snapshot(name='qt')
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')
        assert (CONFIGS / 'dolphin-emu' / 'Hotkeys.ini').read_text() == snapshot(name='hotkeys')
        assert (CONFIGS / 'dolphin-emu' / 'RetroAchievements.ini').read_text() == snapshot(name='ra')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')

    def test_generate_sysconf(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF',
            contents=_sysconf(
                _big_array('BAT.BGA', b'\x04' * 17),
                _byte('IPL.LNG', 10),
                _small_array('BAT.SMA', b'\x01' * 16),
                _byte('IPL.AR', 4),
                _short('BAT.SRT', 16),
                _long('BAT.LNG', 4096),
                _long_long('BAT.LL', 268435456),
                _bool('BAT.BOL', True),
                _byte('BAT.BYT', 42),
                _byte('BT.BAR', 2),
            ),
        )

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF').read_bytes() == snapshot

    @pytest.mark.parametrize(
        'sysconf_item',
        [
            pytest.param(['BAT.ERR', 0, b'\x00'], id='unknown'),
            pytest.param(_short('IPL.AR', 4), id='not writable'),
        ],
    )
    def test_generate_sysconf_raises(
        self,
        generator: Generator,
        sysconf_item: tuple[str, int, bytes],
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF',
            contents=_sysconf(_byte('IPL.LNG', 10), sysconf_item, _byte('BT.BAR', 2)),
        )

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF').read_bytes() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'tv_mode': '0'},
            {'tv_mode': '1'},
            {'sensorbar_position': '0'},
            {'sensorbar_position': '1'},
        ],
        ids=str,
    )
    def test_generate_sysconf_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF',
            contents=_sysconf(
                _byte('IPL.AR', 4),
                _byte('BT.BAR', 2),
            ),
        )

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF').read_bytes() == snapshot

    @pytest.mark.parametrize(
        'os_environ_lang',
        ['jp_JP', 'en_US', 'de_DE', 'fr_FR', 'es_ES', 'it_IT', 'nl_NL', 'zh_CN', 'zh_TW', 'ko_KR', 'en_GB'],
        indirect=True,
    )
    def test_generate_sysconf_lang(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF',
            contents=_sysconf(
                _byte('IPL.LNG', 10),
            ),
        )

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'dolphin-emu' / 'Wii' / 'shared2' / 'sys' / 'SYSCONF').read_bytes() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'incrementalsavestates': '1'},
            {'incrementalsavestates': '0'},
            {'state_slot': '1'},
            {'ShowDpMsg': '1'},
            {'ShowDpMsg': '0'},
            {'enable_cheats': '1'},
            {'enable_cheats': '0'},
            {'enable_fastdisc': '1'},
            {'enable_fastdisc': '0'},
            {'dual_core': '1'},
            {'dual_core': '0'},
            {'gpu_sync': '1'},
            {'gpu_sync': '0'},
            {'enable_mmu': '1'},
            {'enable_mmu': '0'},
            {'dplii': '1'},
            {'dplii': '0'},
            {'dolphin_aspect_ratio': '1'},
            {'showFPS': '1'},
            {'showFPS': '0'},
            {'hires_textures': '1'},
            {'hires_textures': '0'},
            {'ubershaders': '0'},
            {'ubershaders': '1'},
            {'wait_for_shaders': '1'},
            {'wait_for_shaders': '1', 'gfxbackend': 'Vulkan'},
            {'wait_for_shaders': '1', 'gfxbackend': 'OGL'},
            {'wait_for_shaders': '0'},
            {'perf_hacks': '1'},
            {'perf_hacks': '0'},
            {'vbi_hack': '1'},
            {'vbi_hack': '0'},
            {'internal_resolution': '2'},
            {'vsync': '1'},
            {'vsync': '0'},
            {'gfxbackend': 'OGL'},
            {'gfxbackend': 'Vulkan'},
            {'anisotropic_filtering': '1'},
            {'antialiasing': '2'},
            {'use_ssaa': '1'},
            {'use_ssaa': '0'},
            {'manual_texture_sampling': '1'},
            {'manual_texture_sampling': '0'},
            {'state_filename': 'foo.state'},
        ],
        ids=str,
    )
    def test_generate_config(self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'gamecube' / 'rom.gcz',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'dolphin-emu' / 'Qt.ini').read_text() == snapshot(name='qt')
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'widescreen_hack': '1'},
            {'widescreen_hack': '0'},
            {'widescreen_hack': '1', 'enable_cheats': '0'},
            {'widescreen_hack': '1', 'enable_cheats': '1'},
            {'gamecube_language': '1'},
        ],
        ids=str,
    )
    def test_generate_config_gamecube(
        self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')

    @pytest.mark.system_name('wii')
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'dsmotion': '0'},
            {'dsmotion': '1'},
            {'mouseir': '0'},
            {'mouseir': '1'},
        ],
        ids=str,
    )
    def test_generate_config_wii(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'wii' / 'rom.gcz',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'WiimoteNew.ini').read_text() == snapshot(name='wiimote')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            pytest.param({'retroachievements': '1'}, id='enabled'),
            pytest.param(
                {
                    'retroachievements': '1',
                    'retroachievements.username': 'username',
                    'retroachievements.token': 'token',
                    'retroachievements.hardcore': '1',
                    'retroachievements.richpresence': '1',
                    'retroachievements.leaderboard': '1',
                    'retroachievements.challenge_indicators': '1',
                    'retroachievements.encore': '1',
                    'retroachievements.verbose': '1',
                    'retroachievements.unofficial': '1',
                },
                id='enabled, with non-default options',
            ),
        ],
    )
    def test_generate_retroachievements(
        self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'RetroAchievements.ini').read_text() == snapshot(name='ra')

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            'en_US',
            'de_DE',
            'fr_FR',
            'es_ES',
            'it_IT',
            'nl_NL',
            'en_GB',
        ],
        indirect=True,
    )
    def test_generate_gamecube_lang_from_environment(
        self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')

    @pytest.mark.mock_system_config({'gfxbackend': 'Vulkan'})
    @pytest.mark.parametrize(
        ('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index'),
        [
            pytest.param(False, False, None, id='vulkan unavailable'),
            pytest.param(True, False, None, id='vulkan available, no discrete gpu'),
            pytest.param(True, True, None, id='vulkan available, no discrete gpu index'),
            pytest.param(True, True, '4', id='vulkan available'),
        ],
        indirect=True,
    )
    def test_generate_vulkan(self, generator: Generator, mock_system: Emulator, snapshot: SnapshotAssertion) -> None:
        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')

    @pytest.mark.system_name('wii')
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'emulatedwiimotes': '0'},
            {'emulatedwiimotes': '1'},
            {'emulatedwiimotes': '1', 'controller_mode': 'disabled'},
            {'emulatedwiimotes': '1', 'controller_mode': 'cc'},
            {'emulatedwiimotes': '1', 'controller_mode': 'pro'},
            {'emulatedwiimotes': '1', 'controller_mode': 'side'},
            {'emulatedwiimotes': '1', 'controller_mode': 'is'},
            {'emulatedwiimotes': '1', 'controller_mode': 'it'},
            {'emulatedwiimotes': '1', 'controller_mode': 'in'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize(
        'rom_infix',
        ['cc', 'pro', 'side', 'is', 'it', 'in', 'ti', 'ts', 'tn', 'ni', 'ns', 'nt', 'si', 'st', 'sn'],
    )
    def test_generate_wii_emulated_wiimotes(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        rom_infix: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'dolphin-emu' / 'GCPadNew.ini', encoding='utf_8_sig', contents="""old controller config"""
        )

        generator.generate(
            mock_system,
            ROMS / 'wii' / f'rom.{rom_infix}.gcz',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'WiimoteNew.ini').read_text() == snapshot(name='wiimote')
        if mock_system.config.get('emulatedwiimotes') == '0' or (
            'emulatedwiimotes' not in mock_system.config and rom_infix in ('si', 'st', 'sn')
        ):
            assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')
        else:
            assert not (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').exists()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'rumble': '1'},
            {'rumble': '0'},
            {'deadzone_1': '0.0', 'deadzone_2': '10.0', 'deadzone_3': '20.0', 'deadzone_4': '30.0'},
            {
                'jsgate_size_1': 'normal',
                'jsgate_size_2': 'larger',
                'jsgate_size_3': 'normal',
                'jsgate_size_4': 'smaller',
            },
        ],
        ids=str,
    )
    @pytest.mark.parametrize('system_name', ['gamecube', 'wii'])
    def test_generate_controllers(
        self,
        generator: Generator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(
            generic_xbox_pad, ps3_controller, generic_xbox_pad, keyboard_controller, generic_xbox_pad
        )

        generator.generate(
            mock_system,
            ROMS / mock_system.name / 'rom.gcz',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (
            CONFIGS / 'dolphin-emu' / ('WiimoteNew.ini' if mock_system.name == 'wii' else 'GCPadNew.ini')
        ).read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {
                'dolphin_port_1_type': '6a',
                'dolphin_port_2_type': '6b',
                'dolphin_port_3_type': '12',
                'dolphin_port_4_type': '0',
            },
            {
                'dolphin_port_1_type': '6a',
                'dolphin_port_2_type': '6b',
                'dolphin_port_3_type': '12',
                'dolphin_port_4_type': '0',
                'alt_mappings_1': '1',
                'alt_mappings_2': '1',
                'alt_mappings_3': '1',
                'alt_mappings_4': '1',
            },
        ],
        ids=str,
    )
    @pytest.mark.parametrize('system_name', ['gamecube', 'wii'])
    def test_generate_controller_type(
        self,
        generator: Generator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(
            generic_xbox_pad, ps3_controller, generic_xbox_pad, ps3_controller, generic_xbox_pad
        )

        generator.generate(
            mock_system,
            ROMS / mock_system.name / 'rom.gcz',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')
        if mock_system.name == 'wii':
            assert (CONFIGS / 'dolphin-emu' / 'WiimoteNew.ini').read_text() == snapshot(name='wiimote')

    @pytest.mark.system_name('wii')  # The guns config is only able to be set for Wii
    @pytest.mark.parametrize(
        ('mock_system_config', 'metadata', 'need_cross'),
        [
            pytest.param({}, {}, False, id='no config, no metadata, no cross'),
            pytest.param({}, {}, True, id='no config, no metadata, needs cross'),
            pytest.param(
                {},
                {
                    'gun_ir_up': 'up value',
                    'gun_ir_down': 'down value',
                    'gun_ir_left': 'left value',
                    'gun_ir_right': 'right value',
                },
                False,
                id='no config, ir_* in metadata, no cross',
            ),
            pytest.param(
                {},
                {
                    'gun_action': 'z,shake',
                    'gun_start': 'tiltleft',
                    'gun_select': 'a',
                    'gun_sub1': '+',
                    'gun_sub2': 'foo',
                },
                False,
                id='no config, ir_* in metadata, no cross',
            ),
            pytest.param(
                {'dolphin_crosshair': '1'},
                {
                    'gun_action': 'z,shake',
                    'gun_start': 'tiltleft',
                    'gun_select': 'a',
                    'gun_sub1': '+',
                    'gun_sub2': 'foo',
                },
                False,
                id='show crosshairs config, ir_* in metadata, no cross',
            ),
            pytest.param(
                {'dolphin_crosshair': '1'},
                {
                    'gun_action': 'z,shake',
                    'gun_start': 'tiltleft',
                    'gun_select': 'a',
                    'gun_sub1': '+',
                    'gun_sub2': 'foo',
                },
                True,
                id='show crosshairs config, ir_* in metadata, needs cross',
            ),
            pytest.param(
                {'dolphin_crosshair': '0'},
                {
                    'gun_action': 'z,shake',
                    'gun_start': 'tiltleft',
                    'gun_select': 'a',
                    'gun_sub1': '+',
                    'gun_sub2': 'foo',
                },
                False,
                id='hide crosshairs config, ir_* in metadata, no cross',
            ),
            pytest.param(
                {'dolphin_crosshair': '0'},
                {
                    'gun_action': 'z,shake',
                    'gun_start': 'tiltleft',
                    'gun_select': 'a',
                    'gun_sub1': '+',
                    'gun_sub2': 'foo',
                },
                False,
                id='hide crosshairs config, ir_* in metadata, needs cross',
            ),
        ],
        ids=str,
    )
    def test_generate_guns(
        self,
        generator: Generator,
        mock_system: Emulator,
        metadata: dict[str, Any],
        need_cross: bool,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(generic_xbox_pad)
        mock_system.config['use_guns'] = '1'

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            controllers,
            metadata,
            [
                Gun(
                    node='/dev/input/event42',
                    mouse_index=-1,
                    needs_cross=False,
                    needs_borders=False,
                    name='gun 0',
                    buttons=['left', 'right', 'middle', '1', '2', '3'],
                ),
                Gun(
                    node='/dev/input/event43',
                    mouse_index=-1,
                    needs_cross=False,
                    needs_borders=False,
                    name='gun 0',
                    buttons=['left', 'right', 'middle', '1', '2', '3'],
                ),
                Gun(
                    node='/dev/input/event44',
                    mouse_index=-1,
                    needs_cross=False,
                    needs_borders=False,
                    name='gun 2',
                    buttons=['left', 'right', 'middle', '1', '2', '3'],
                ),
                Gun(
                    node='/dev/input/event45',
                    mouse_index=-1,
                    needs_cross=need_cross,
                    needs_borders=False,
                    name='gun 3',
                    buttons=['left', 'right', 'middle', '1', '2', '3'],
                ),
                Gun(
                    node='/dev/input/event46',
                    mouse_index=-1,
                    needs_cross=False,
                    needs_borders=False,
                    name='gun 4',
                    buttons=['left', 'right', 'middle', '1', '2', '3'],
                ),
            ],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GFX.ini').read_text() == snapshot(name='gfx')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')
        assert (CONFIGS / 'dolphin-emu' / 'WiimoteNew.ini').read_text() == snapshot(name='wiimote')

    @pytest.mark.parametrize(
        'metadata',
        [
            {},
            {'wheel_type': 'Steering Wheel'},
            {'wheel_type': 'Foo'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'dolphin_wheel_type': 'Steering Wheel'},
            {'dolphin_wheel_type': 'Foo'},
        ],
        ids=str,
    )
    def test_generate_wheels(
        self,
        generator: Generator,
        mock_system: Emulator,
        metadata: dict[str, Any],
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(
            generic_xbox_pad, ps3_controller, generic_xbox_pad, ps3_controller, generic_xbox_pad
        )
        mock_system.config['use_wheels'] = '1'

        generator.generate(
            mock_system,
            ROMS / mock_system.name / 'rom.gcz',
            controllers,
            metadata,
            [],
            {'/dev/input/event2': cast('DeviceInfo', {})},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'dolphin-emu' / 'GCPadNew.ini').read_text() == snapshot(name='gcpad')
        assert not (CONFIGS / 'dolphin-emu' / 'WiimoteNew.ini').exists()

    @pytest.mark.parametrize(
        ('mock_system_config', 'bios_region'),
        [
            pytest.param({'dolphin_SkipIPL': '0'}, None, id='skip off'),
            pytest.param({'dolphin_SkipIPL': '1'}, None, id='skip on, no bios files'),
            pytest.param({'dolphin_SkipIPL': '1'}, 'USA', id='skip on, USA bios file'),
            pytest.param({'dolphin_SkipIPL': '1'}, 'EUR', id='skip on, EUR bios file'),
            pytest.param({'dolphin_SkipIPL': '1'}, 'JAP', id='skip on, JAP bios file'),
            pytest.param({'dolphin_SkipIPL': '1'}, 'foo', id='skip on, foo bios file'),
        ],
    )
    def test_generate_skip_boot_animation(
        self,
        generator: Generator,
        bios_region: str | None,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        if bios_region is not None:
            fs.create_file(BIOS / 'GC' / bios_region / 'IPL.bin')

        generator.generate(
            mock_system,
            ROMS / 'gamecube' / 'rom.gcz',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'dolphin-emu' / 'Dolphin.ini').read_text() == snapshot(name='config')
