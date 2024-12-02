from __future__ import annotations

import filecmp
import io
import stat
import tarfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from pytest_lazy_fixtures import lf

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.lindbergh.lindberghGenerator import LindberghGenerator
from configgen.utils.download import DownloadException
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


def _add_file_to_tarfile(tar: tarfile.TarFile, name: str, contents: str, /) -> None:
    encoded = contents.encode()
    info = tarfile.TarInfo(name)
    info.size = len(encoded)
    tar.addfile(info, io.BytesIO(encoded))


class TestLindberghGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return LindberghGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'lindbergh'

    @pytest.fixture
    def emulator(self) -> str:
        return 'lindbergh-loader'

    @pytest.fixture(autouse=True)
    def evdev(self, evdev: Mock) -> Mock:
        evdev.ecodes.KEY_T = 20
        evdev.ecodes.BTN_1 = 0x101
        evdev.ecodes.BTN_2 = 0x102
        evdev.ecodes.BTN_3 = 0x103
        evdev.ecodes.BTN_4 = 0x104
        evdev.ecodes.BTN_5 = 0x105
        evdev.ecodes.BTN_6 = 0x106
        evdev.ecodes.BTN_7 = 0x107
        evdev.ecodes.BTN_8 = 0x108
        evdev.ecodes.BTN_LEFT = 0x110
        evdev.ecodes.BTN_RIGHT = 0x111
        evdev.ecodes.BTN_MIDDLE = 0x112
        return evdev

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/lib32/libkswapapi.so', contents='libkswapapi.so')
        fs.create_file('/lib32/extralibs/libCg.so.harley', contents='libCg.so.harley')
        fs.create_file('/lib32/extralibs/libCgGL.so.harley', contents='libCgGL.so.harley')
        fs.create_file('/lib32/extralibs/libCg.so.other', contents='libCg.so.other')
        fs.create_file('/lib32/extralibs/libCgGL.so.other', contents='libCgGL.so.other')
        fs.create_file('/lib32/extralibs/libCg.so.tennis', contents='libCg.so.tennis')
        fs.create_file('/lib32/extralibs/libCgGL.so.tennis', contents='libCgGL.so.tennis')
        fs.create_file(SAVES / 'lindbergh' / 'downloaded.txt', contents='Download and extraction successful.\n')
        fs.create_file('/usr/bin/lindbergh/lindbergh', contents='lindbergh bin')
        fs.create_file('/usr/bin/lindbergh/lindbergh.so', contents='lindbergh lib')
        fs.add_real_file(
            Path(__file__).parent / '__files__' / 'lindbergh.conf', target_path='/usr/bin/lindbergh/lindbergh.conf'
        )
        return fs

    @pytest.fixture
    def download(self, mocker: MockerFixture) -> Mock:
        tar_content = io.BytesIO()

        with tarfile.open(fileobj=tar_content, mode='w:xz') as tar:
            _add_file_to_tarfile(tar, 'foo.txt', 'foo contents')
            _add_file_to_tarfile(tar, 'bar.txt', 'bar contents')

        tar_content.seek(0)

        download = mocker.patch('configgen.generators.lindbergh.lindberghGenerator.download')
        download.return_value.__enter__.return_value = tar_content

        return download

    @pytest.fixture(autouse=True)
    def socket_socket(self, mocker: MockerFixture) -> Mock:
        mock_socket = mocker.MagicMock()
        mock_socket.__enter__.return_value = mock_socket
        mock_socket.getsockname.return_value = ('2.2.2.2',)

        return mocker.patch('socket.socket', return_value=mock_socket)

    @pytest.fixture(autouse=True)
    def get_hotkeygen_event(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.hotkeygen.get_hotkeygen_event', return_value=None)

    @pytest.fixture(autouse=True)
    def get_mapping_axis_relaxed_values(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.controller.Controller.get_mapping_axis_relaxed_values', return_value={})

    def test_get_in_game_ratio(self, generator: Generator) -> None:
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh', '/usr/bin/lindbergh/lindbergh')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.so', '/usr/bin/lindbergh/lindbergh.so')
        assert filecmp.cmp(
            ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf', '/userdata/system/configs/lindbergh/lindbergh.conf'
        )
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1', '/lib32/libkswapapi.so')
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so').exists()
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so').exists()

    def test_generate_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'lindbergh' / 'lindbergh.conf',
            contents="""# SEGA Lindbergh Emulator Configuration File
# By the Lindbergh Development Team

# Set the requested dip switch width here
WIDTH 40

# Set the requested dip switch height here
HEIGHT 40

# Set if the emulator should go full screen
FULLSCREEN 2

# Sets the Input Mode
# Mode 0: will use both SDL/X11 and EVDEV inputs (default)
# Mode 1: will use SDL/X11 inputs only
# Mode 2: will use EVDEV raw inputs only, which should be configured at the bottom of the settings file
INPUT_MODE 0

# Set to 1 if you want to disable SDL (Fixes SRTV boost bar)
# NO_SDL 0
NO_SDL 1

# Set the Region ( JP/US/EX )
REGION US
# REGION JP

# Set if you want the game to be Free Play
FREEPLAY 0
FREEPLAY 1

EMULATE_CARDREADER 1
""",
        )
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1')
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libsegaapi.so')
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')
        fs.create_file('/userdata/roms/lindbergh/rom_dir/lindbergh')
        fs.create_file('/userdata/roms/lindbergh/rom_dir/lindbergh.so')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1', '/lib32/libkswapapi.so')
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh', '/usr/bin/lindbergh/lindbergh')
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.so', '/usr/bin/lindbergh/lindbergh.so')
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so').exists()
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so').exists()
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libsegaapi.so').exists()

    def test_generate_missing_libkswapapi(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        fs.remove('/lib32/libkswapapi.so')
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not (ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1').exists()

    def test_generate_download(
        self, fs: FakeFilesystem, generator: Generator, mock_system: Emulator, download: Mock
    ) -> None:
        fs.remove(str(SAVES / 'lindbergh' / 'downloaded.txt'))
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'lindbergh' / 'foo.txt').read_text() == 'foo contents'
        assert (SAVES / 'lindbergh' / 'bar.txt').read_text() == 'bar contents'
        assert (SAVES / 'lindbergh' / 'downloaded.txt').exists()
        download.assert_called_once_with(
            'https://raw.githubusercontent.com/batocera-linux/lindbergh-eeprom/main/lindbergh-eeprom.tar.xz',
            SAVES / 'lindbergh',
        )

    @pytest.mark.usefixtures('download')
    def test_generate_download_existing_files(
        self, fs: FakeFilesystem, generator: Generator, mock_system: Emulator
    ) -> None:
        fs.remove(str(SAVES / 'lindbergh' / 'downloaded.txt'))
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')
        fs.create_file(SAVES / 'lindbergh' / 'foo.txt', contents='existing foo contents')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'lindbergh' / 'foo.txt').read_text() == 'existing foo contents'
        assert (SAVES / 'lindbergh' / 'bar.txt').read_text() == 'bar contents'

    @pytest.mark.usefixtures('download')
    def test_generate_download_error_response(
        self, fs: FakeFilesystem, generator: Generator, download: Mock, mock_system: Emulator
    ) -> None:
        download.side_effect = DownloadException

        fs.remove(str(SAVES / 'lindbergh' / 'downloaded.txt'))
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert not (SAVES / 'lindbergh' / 'foo.txt').exists()
        assert not (SAVES / 'lindbergh' / 'bar.txt').exists()
        assert not (SAVES / 'lindbergh' / 'downloaded.txt').exists()
        assert not (SAVES / 'lindbergh' / 'lindbergh-eeprom.tar.xz').exists()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'lindbergh_freeplay': '0'},
            {'lindbergh_freeplay': '1'},
            {'lindbergh_region': 'US'},
            {'lindbergh_aspect': '0'},
            {'lindbergh_aspect': '1'},
            {'lindbergh_limit': '0'},
            {'lindbergh_limit': '1'},
            {'lindbergh_fps': '30'},
            {'lindbergh_controller': '1'},
            {'lindbergh_hummer': '0'},
            {'lindbergh_hummer': '1'},
            {'lindbergh_lens': '0'},
            {'lindbergh_lens': '1'},
            {'lindbergh_test': '0'},
            {'lindbergh_test': '1'},
            {'lindbergh_debug': '0'},
            {'lindbergh_debug': '1'},
            {'lindbergh_zink': '0'},
            {'lindbergh_zink': '1'},
            {'lindbergh_boost': '0'},
            {'lindbergh_boost': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('mock_system_config', [{}, {'lindbergh_card': '0'}, {'lindbergh_card': '1'}], ids=str)
    def test_generate_tennis(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/lindbergh/Virtua Tennis 3/vtennis3.game')
        fs.create_file('/userdata/roms/lindbergh/Virtua Tennis 3/vt3_Lindbergh')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'vtennis3.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'lindbergh.conf').read_text() == snapshot(name='config')
        assert stat.filemode((ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'vt3_Lindbergh').stat().st_mode) == snapshot(
            name='executable mode'
        )
        assert filecmp.cmp(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libGLcore.so.1', '/lib32/libkswapapi.so')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCg.so', '/lib32/extralibs/libCg.so.other')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.other')

    def test_generate_tennis_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        fs.create_file(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCg.so')
        fs.create_file(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCgGL.so')
        fs.create_file('/userdata/roms/lindbergh/Virtua Tennis 3/vtennis3.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'vtennis3.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCg.so', '/lib32/extralibs/libCg.so.other')
        assert not filecmp.cmp(
            ROMS / 'lindbergh' / 'Virtua Tennis 3' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.other'
        )

    @pytest.mark.parametrize('rom_name', ['harley', 'hdkotr', 'spicy', 'rambo', 'hotdex', 'dead ex'])
    def test_generate_harley(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        rom_name: str,
    ) -> None:
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1', '/lib32/libkswapapi.so')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so', '/lib32/extralibs/libCg.so.harley')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.harley')

    @pytest.mark.parametrize('rom_name', ['harley', 'hdkotr', 'spicy', 'rambo', 'hotdex', 'dead ex'])
    def test_generate_harley_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        rom_name: str,
    ) -> None:
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so')
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so')
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so', '/lib32/extralibs/libCg.so.harley')
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.harley')

    @pytest.mark.parametrize('rom_name', ['letsgoju', 'letsgojusp', 'initiad4'])
    def test_generate_initial_d(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        rom_name: str,
    ) -> None:
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libGLcore.so.1', '/lib32/libkswapapi.so')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so', '/lib32/extralibs/libCg.so.other')
        assert filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.other')

    @pytest.mark.parametrize('rom_name', ['letsgoju', 'letsgojusp', 'initiad4'])
    def test_generate_initial_d_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        rom_name: str,
    ) -> None:
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so')
        fs.create_file(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so')
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCg.so', '/lib32/extralibs/libCg.so.other')
        assert not filecmp.cmp(ROMS / 'lindbergh' / 'rom_dir' / 'libCgGL.so', '/lib32/extralibs/libCgGL.so.other')

    @pytest.mark.parametrize('succeed_on_try', [0, 1, 2])
    @pytest.mark.mock_system_config({'lindbergh_ip': '1'})
    def test_generate_outrun(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        socket_socket: Mock,
        succeed_on_try: int,
        snapshot: SnapshotAssertion,
    ) -> None:
        if succeed_on_try != 1:
            socket_socket.return_value.getsockname.side_effect = (
                Exception('Test exception') if not succeed_on_try else [Exception('Test exception'), ('3.3.3.3',)]
            )
        fs.create_file('/userdata/roms/lindbergh/rom_dir/outr2sdx.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'outr2sdx.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('speed_value', ['0.5', '4.0', '3.1'])
    @pytest.mark.parametrize('rom_name', ['hotd4', 'hotd4sp'])
    def test_generate_hotd_cpu_speed(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        rom_name: str,
        speed_value: str | None,
        snapshot: SnapshotAssertion,
    ) -> None:
        if speed_value is not None:
            mock_system.config['lindbergh_speed'] = speed_value

        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    def test_generate_hotkeygen_device(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        get_hotkeygen_event: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        get_hotkeygen_event.return_value = '/dev/input/event42'
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom_name',
        [
            'rom',
            'hdkotr',
            'rtuned',
            'initiad4ex',
            'initiad4exb',
            'hummer',
            'hummerxt',
            'segartv',
            'outr2sdx',
            'outr2sdxg',
        ],
    )
    def test_generate_controllers(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        rom_name: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    def test_generate_controllers_relaxed_values(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        get_mapping_axis_relaxed_values: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/lindbergh/rom_dir/rom.game')

        get_mapping_axis_relaxed_values.side_effect = [
            {
                'joystick1left': {'centered': False, 'reversed': True},
                'joystick1up': {'centered': False, 'reversed': False},
            },
            {},
        ]

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / 'rom.game',
            make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom_name',
        [
            'rom',
            'hdkotr',
            'rtuned',
            'initiad4ex',
            'initiad4exb',
            'hummer',
            'hummerxt',
            'segartv',
            'outr2sdx',
            'outr2sdxg',
            'vf5',
            'vf5c',
        ],
    )
    @pytest.mark.mock_system_config({'use_wheels': '1'})
    def test_generate_wheels(
        self,
        mocker: MockerFixture,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        g920_wheel: Controller,
        rom_name: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            make_player_controller_list(g920_wheel, g920_wheel, g920_wheel),
            {},
            [],
            {
                '/dev/input/event1': mocker.Mock(),
                '/dev/input/event2': mocker.Mock(),
                '/dev/input/event3': mocker.Mock(),
            },
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'controllers', [[lf('xtension_2p_p1'), lf('xtension_2p_p1')], [lf('generic_xbox_pad'), lf('ps3_controller')]]
    )
    @pytest.mark.parametrize(
        'rom_name',
        [
            'rom',
            'hdkotr',
            'rtuned',
            'initiad4ex',
            'initiad4exb',
            'hummer',
            'hummerxt',
            'segartv',
            'outr2sdx',
            'outr2sdxg',
            'vf5',
            'vf5c',
        ],
    )
    @pytest.mark.mock_system_config({'use_wheels': '1'})
    def test_generate_wheels_no_real_wheels(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        controllers: list[Controller],
        generic_xbox_pad: Controller,
        rom_name: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(f'/userdata/roms/lindbergh/rom_dir/{rom_name}.game')

        generator.generate(
            mock_system,
            ROMS / 'lindbergh' / 'rom_dir' / f'{rom_name}.game',
            make_player_controller_list(*controllers, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'lindbergh' / 'rom_dir' / 'lindbergh.conf').read_text() == snapshot(name='config')
