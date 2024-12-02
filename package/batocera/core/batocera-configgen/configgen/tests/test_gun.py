from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BATOCERA_SHARE_DIR, CONFIGS, ROMS, SAVES
from configgen.gun import Gun, guns_need_crosses

if TYPE_CHECKING:
    from _typeshed import StrPath
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

    from configgen.Emulator import Emulator

pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture(autouse=True)
def evdev(evdev: Mock) -> Mock:
    evdev.ecodes.EV_KEY = 0x01
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


@pytest.mark.parametrize(
    ('guns', 'expected'),
    [
        pytest.param([], True, id='no guns'),
        pytest.param([False, True], True, id='at least one gun needs crosses'),
        pytest.param([False, False], False, id='no guns need crosses'),
    ],
)
def test_guns_need_crosses(mocker: MockerFixture, guns: list[bool], expected: bool) -> None:
    assert guns_need_crosses([mocker.Mock(needs_cross=value) for value in guns]) == expected


class TestGun:
    @pytest.fixture
    def gun_get_all(self, mocker: MockerFixture) -> Mock:
        return mocker.patch.object(Gun, 'get_all', return_value=mocker.sentinel.get_all)

    @pytest.mark.parametrize(
        ('buttons', 'expected'),
        [
            (
                ['left', 'right', 'middle', '1', '2', '3', '4', '5', '6', '7', '8'],
                {
                    'left': 0x110,
                    'right': 0x111,
                    'middle': 0x112,
                    '1': 0x101,
                    '2': 0x102,
                    '3': 0x103,
                    '4': 0x104,
                    '5': 0x105,
                    '6': 0x106,
                    '7': 0x107,
                    '8': 0x108,
                },
            ),
            (['left', 'right', 'middle'], {'left': 0x110, 'right': 0x111, 'middle': 0x112}),
            (['foo', 'bar', 'baz'], {}),
        ],
    )
    def test_button_map(self, buttons: list[str], expected: dict[str, int]) -> None:
        assert (
            Gun(node='', mouse_index=-1, needs_cross=False, needs_borders=False, name='gun', buttons=buttons).button_map
            == expected
        )

    def test_get_all(self, mocker: MockerFixture, pyudev: Mock, evdev: Mock) -> None:
        context_instance = mocker.Mock()

        context_instance.list_devices.return_value = [
            mocker.Mock(device_node='/dev/foo'),
            mocker.Mock(device_node='/dev/input/event0', properties={}),
            mocker.Mock(device_node='/dev/input/event1', properties={'ID_INPUT_MOUSE': '1'}),
            mocker.Mock(device_node='/dev/input/event2', properties={'ID_INPUT_MOUSE': '1', 'ID_INPUT_GUN': '1'}),
            mocker.Mock(device_node='/dev/input/event3', properties={'ID_INPUT_MOUSE': '1'}),
            mocker.Mock(
                device_node='/dev/input/event4',
                properties={'ID_INPUT_MOUSE': '1', 'ID_INPUT_GUN': '1', 'ID_INPUT_GUN_NEED_CROSS': '1'},
            ),
            mocker.Mock(
                device_node='/dev/input/event5',
                properties={'ID_INPUT_MOUSE': '1', 'ID_INPUT_GUN': '1', 'ID_INPUT_GUN_NEED_BORDERS': '1'},
            ),
        ]

        pyudev.Context.return_value = context_instance

        capabilities = {
            '/dev/input/event2': {1: [0x110, 1, 2, 3]},
            '/dev/input/event4': {1: [0x101, 0x103, 0x102, 0x104, 0x105, 0x106, 0x107, 0x108, 0x110, 0x111, 0x112]},
            '/dev/input/event5': {1: [0x110, 1, 2, 3, 0x102]},
        }

        def input_device_side_effect(device_node: str) -> Mock:
            device = mocker.Mock()
            device.name = device_node.split('/')[-1]
            device.capabilities.return_value = capabilities.get(device_node) or {1: {}}
            return device

        evdev.InputDevice.side_effect = input_device_side_effect

        assert Gun.get_all() == [
            Gun(
                node='/dev/input/event2',
                mouse_index=1,
                needs_cross=False,
                needs_borders=False,
                name='event2',
                buttons=['left'],
            ),
            Gun(
                node='/dev/input/event4',
                mouse_index=3,
                needs_cross=True,
                needs_borders=False,
                name='event4',
                buttons=['left', 'right', 'middle', '1', '2', '3', '4', '5', '6', '7', '8'],
            ),
            Gun(
                node='/dev/input/event5',
                mouse_index=4,
                needs_cross=False,
                needs_borders=True,
                name='event5',
                buttons=['left', '2'],
            ),
        ]

    def test_get_all_no_guns(self, mocker: MockerFixture, pyudev: Mock) -> None:
        context_instance = mocker.Mock()

        context_instance.list_devices.return_value = [
            mocker.Mock(device_node='/dev/foo'),
            mocker.Mock(device_node='/dev/input/event0', properties={}),
            mocker.Mock(device_node='/dev/input/event1', properties={'ID_INPUT_MOUSE': '1'}),
            mocker.Mock(device_node='/dev/input/event3', properties={'ID_INPUT_MOUSE': '1'}),
        ]

        pyudev.Context.return_value = context_instance

        assert Gun.get_all() == []

    @pytest.mark.parametrize('mock_system_config', [{}, {'use_guns': False}])
    def test_get_and_precalibrate_all_guns_disabled(self, mock_system: Emulator) -> None:
        assert Gun.get_and_precalibrate_all(mock_system, '') == []

    @pytest.mark.parametrize(
        'source_files',
        [
            None,
            ['rom.zip.nvmem'],
            ['rom.zip.nvmem', 'rom.zip.nvmem2'],
        ],
    )
    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.emulator('flycast')
    @pytest.mark.system_name('atomiswave')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_atomiswave(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator, source_files: list[StrPath] | None
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'atomiswave')

        if source_files:
            for file in source_files:
                fs.create_file(
                    BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'atomiswave' / 'reicast' / file,
                    contents=f'source file {file}',
                )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'atomiswave' / 'rom.zip') == mocker.sentinel.get_all

        if not source_files:
            assert not SAVES.exists()
            assert not CONFIGS.exists()
        else:
            for file in source_files:
                assert SAVES / 'atomiswave' / 'reicast' / file

    @pytest.mark.parametrize(
        'source_files',
        [
            None,
            ['nvram/rom/nvram', 'nvram/rom/stuff.eeprom'],
            ['diff/rom_v1.00.dif', 'diff/rom_v2.00.dif', 'diff/foo_v1.00.dif'],
        ],
    )
    @pytest.mark.parametrize(
        ('emulator', 'core', 'target_dir'),
        [
            ('mame', None, 'mame'),
            ('libretro', 'mame078plus', 'mame/mame2003-plus'),
            ('libretro', 'mame', 'mame/mame'),
            ('foo', None, None),
            ('libretro', 'foo', None),
        ],
    )
    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.system_name('mame')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_mame(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        mock_system: Emulator,
        target_dir: str | None,
        source_files: list[StrPath] | None,
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'mame' / 'nvram')
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'mame' / 'diff')

        if source_files:
            for file in source_files:
                fs.create_file(
                    BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'mame' / file,
                    contents=f'source file {file}',
                )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'mame' / 'rom.zip') == mocker.sentinel.get_all

        if not source_files:
            assert not SAVES.exists()
            assert not CONFIGS.exists()
        else:
            if not target_dir:
                assert not SAVES.exists()
                assert not CONFIGS.exists()
            else:
                for file in source_files:
                    if str(file).endswith('foo_v1.00.dif'):
                        assert not (SAVES / target_dir / file).exists()
                    else:
                        assert (SAVES / target_dir / file).exists()

    @pytest.mark.parametrize(
        'source_files',
        [
            None,
            ['rom.zip.nvmem'],
            ['rom.zip.nvmem', 'rom.zip.nvmem2'],
        ],
    )
    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.emulator('flycast')
    @pytest.mark.system_name('naomi')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_naomi(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator, source_files: list[StrPath] | None
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'naomi')

        if source_files:
            for file in source_files:
                fs.create_file(
                    BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'naomi' / 'reicast' / file,
                    contents=f'source file {file}',
                )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'naomi' / 'rom.zip') == mocker.sentinel.get_all

        if not source_files:
            assert not SAVES.exists()
            assert not CONFIGS.exists()
        else:
            for file in source_files:
                assert SAVES / 'naomi' / 'reicast' / file

    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.emulator('model2emu')
    @pytest.mark.system_name('model2')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_model2(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'model2')

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'model2' / 'rom.zip') == mocker.sentinel.get_all

        assert not (SAVES / 'model2' / 'NVDATA' / 'rom.zip.DAT').exists()

        fs.create_file(
            BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'model2' / 'NVDATA' / 'rom.zip.DAT',
            contents='source file',
        )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'model2' / 'rom.zip') == mocker.sentinel.get_all
        assert (SAVES / 'model2' / 'NVDATA' / 'rom.zip.DAT').read_text() == 'source file'

    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.emulator('supermodel')
    @pytest.mark.system_name('supermodel')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_supermodel(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'supermodel')

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'supermodel' / 'rom.zip') == mocker.sentinel.get_all

        assert not (SAVES / 'supermodel' / 'NVDATA' / 'rom.nv').exists()

        fs.create_file(
            BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'supermodel' / 'NVDATA' / 'rom.nv',
            contents='source file',
        )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'supermodel' / 'rom.zip') == mocker.sentinel.get_all
        assert (SAVES / 'supermodel' / 'NVDATA' / 'rom.nv').read_text() == 'source file'

    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.system_name('namco2x6')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_namco2x6(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'namco2x6')

        mock_system.config['emulator'] = 'foobarbaz'
        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'namco2x6' / 'rom.zip') == mocker.sentinel.get_all
        assert not (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').exists()

        mock_system.config['emulator'] = 'play'
        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'namco2x6' / 'rom.zip') == mocker.sentinel.get_all
        assert not (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').exists()

        fs.create_file(
            BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'namco2x6' / 'play' / 'rom',
            contents='source file',
        )

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'namco2x6' / 'rom.zip') == mocker.sentinel.get_all
        assert (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').read_text() == 'source file'

    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.emulator('flycast')
    @pytest.mark.system_name('atomiswave')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_no_source_dir(self, mocker: MockerFixture, mock_system: Emulator) -> None:
        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'atomiswave' / 'rom.zip') == mocker.sentinel.get_all

        assert not SAVES.exists()
        assert not CONFIGS.exists()

    @pytest.mark.usefixtures('gun_get_all')
    @pytest.mark.system_name('foobarbaz')
    @pytest.mark.mock_system_config({'use_guns': True})
    def test_get_and_precalibrate_all_system_does_not_match(
        self, mocker: MockerFixture, fs: FakeFilesystem, mock_system: Emulator
    ) -> None:
        fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'foobarbaz')

        assert Gun.get_and_precalibrate_all(mock_system, ROMS / 'atomiswave' / 'rom.zip') == mocker.sentinel.get_all

        assert not SAVES.exists()
        assert not CONFIGS.exists()
