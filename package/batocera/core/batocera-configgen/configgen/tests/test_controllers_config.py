from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ES_GAMES_METADATA
from configgen.controllersConfig import (
    getAssociatedMouse,
    getDevicesInformation,
    getGamesMetaData,
    getGuns,
    getMouseButtons,
    gunsBorderRatioType,
    gunsBordersSizeName,
    gunsNeedCrosses,
    mouseButtonToCode,
    shortNameFromPath,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.types import DeviceInfoMapping, GunDict


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
        pytest.param({}, True, id='no guns'),
        pytest.param({0: {'need_cross': False}, 1: {'need_cross': True}}, True, id='at least one gun needs crosses'),
        pytest.param({0: {'need_cross': False}, 1: {'need_cross': False}}, False, id='no guns need crosses'),
    ],
)
def test_guns_need_crosses(guns: GunDict, expected: bool) -> None:
    assert gunsNeedCrosses(guns) == expected


@pytest.mark.parametrize('borders_mode', [None, 'normal', 'hidden'])
@pytest.mark.parametrize('es_borders_mode', [None, 'auto', 'normal', 'gameonly', 'hidden'])
@pytest.mark.parametrize('borders_size', [None, 'auto', 'thin', 'medium', 'big'])
@pytest.mark.parametrize(
    'guns',
    [
        pytest.param({}, id='no guns'),
        pytest.param({1: {'need_borders': False}, 2: {'need_borders': False}}, id='guns borders not required'),
        pytest.param({1: {'need_borders': False}, 2: {'need_borders': True}}, id='guns borders required'),
    ],
)
def test_guns_borders_size_name(
    guns: GunDict,
    borders_size: str | None,
    es_borders_mode: str | None,
    borders_mode: str | None,
    snapshot: SnapshotAssertion,
) -> None:
    config: dict[str, str] = {}

    if borders_size is not None:
        config['controllers.guns.borderssize'] = borders_size

    if es_borders_mode is not None:
        config['controllers.guns.bordersmode'] = es_borders_mode

    if borders_mode is not None:
        config['bordersmode'] = borders_mode

    assert gunsBordersSizeName(guns, config) == snapshot


@pytest.mark.parametrize('value', [None, 'foo', '4:3'])
def test_guns_border_ratio_type(value: str | None) -> None:
    assert gunsBorderRatioType({}, {} if value is None else {'controllers.guns.bordersratio': value}) == value


@pytest.mark.parametrize(
    ('codes', 'expected'),
    [
        ([0x101, 0x110, 0x111], ['left', 'right', '1']),
        (
            [0x112, 0x107, 0x105, 0x106, 0x104, 0x103, 0x102, 0x101, 0x108, 0x110, 0x111],
            ['left', 'right', 'middle', '1', '2', '3', '4', '5', '6', '7', '8'],
        ),
        ([], []),
    ],
)
def test_get_mouse_buttons(mocker: MockerFixture, codes: list[int], expected: list[str]) -> None:
    device = mocker.Mock()
    device.capabilities.return_value = {1: [0x100, *codes, 0x109]}

    assert getMouseButtons(device) == expected


@pytest.mark.parametrize(
    ('button', 'code'),
    [
        ('left', 0x110),
        ('right', 0x111),
        ('middle', 0x112),
        ('1', 0x101),
        ('2', 0x102),
        ('3', 0x103),
        ('4', 0x104),
        ('5', 0x105),
        ('6', 0x106),
        ('7', 0x107),
        ('8', 0x108),
        ('foo', None),
    ],
    ids=str,
)
def test_mouse_button_to_code(button: str, code: int | None) -> None:
    assert mouseButtonToCode(button) == code


def test_get_guns(mocker: MockerFixture, pyudev: Mock, evdev: Mock) -> None:
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

    def input_device_side_effect(device_node: str) -> Mock:
        device = mocker.Mock()
        device.name = device_node.split('/')[-1]
        return device

    evdev.InputDevice.side_effect = input_device_side_effect

    mocker.patch('configgen.controllersConfig.getMouseButtons', return_value=['left'])

    assert getGuns() == {
        0: {
            'node': '/dev/input/event2',
            'id_mouse': 1,
            'need_cross': False,
            'need_borders': False,
            'name': 'event2',
            'buttons': ['left'],
        },
        1: {
            'node': '/dev/input/event4',
            'id_mouse': 3,
            'need_cross': True,
            'need_borders': False,
            'name': 'event4',
            'buttons': ['left'],
        },
        2: {
            'node': '/dev/input/event5',
            'id_mouse': 4,
            'need_cross': False,
            'need_borders': True,
            'name': 'event5',
            'buttons': ['left'],
        },
    }


def test_get_guns_no_guns(mocker: MockerFixture, pyudev: Mock) -> None:
    context_instance = mocker.Mock()

    context_instance.list_devices.return_value = [
        mocker.Mock(device_node='/dev/foo'),
        mocker.Mock(device_node='/dev/input/event0', properties={}),
        mocker.Mock(device_node='/dev/input/event1', properties={'ID_INPUT_MOUSE': '1'}),
        mocker.Mock(device_node='/dev/input/event3', properties={'ID_INPUT_MOUSE': '1'}),
    ]

    pyudev.Context.return_value = context_instance

    assert getGuns() == {}


@pytest.mark.parametrize(
    'path',
    [
        '/path/to/ABCDEFGHIGKLMNOPQRSTUVWXYZ!@#$%^&*abcdefghigklmnopqrstuvwxyz!@#$%^&*0123456789!@#$%^&*.zip',
        Path('/another/path/to/AbCdEf@#%!0&.bar.rom'),
        Path('/another/path/to/rom-name [US] suffix.rom'),
        Path('/another/path/to/rom-name (something) suffix.rom'),
        '/userdata/roms/system/blah (something [US]) [EN] (spam) foo.dsk',
    ],
    ids=lambda x: f'Path({x!s})' if isinstance(x, Path) else x,
)
def test_short_name_from_path(path: str | Path, snapshot: SnapshotAssertion) -> None:
    assert shortNameFromPath(path) == snapshot


@pytest.mark.parametrize(
    'rom',
    [
        '/path/to/wheel rom [US].zip',
        Path('/path/to/trackball#rom (US).zip'),
    ],
    ids=lambda x: f'Path({x!s})' if isinstance(x, Path) else x,
)
@pytest.mark.parametrize(
    'system',
    [
        'naomi',
        'naomi2',
        'atomiswave',
        'fbneo',
        'mame',
        'neogeo',
        'triforce',
        'hypseus-singe',
        'model2',
        'model3',
        'hikaru',
        'gaelco',
        'cave3rd',
        'namco2x6',
        'dreamcast',
        'snes',
    ],
)
def test_get_games_meta_data(fs: FakeFilesystem, system: str, rom: str | Path, snapshot: SnapshotAssertion) -> None:
    fs.create_file(
        ES_GAMES_METADATA,
        contents="""<?xml version="1.0" encoding="UTF-8"?>
<systems xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="gamesdb.xsd">
  <system name="arcade">
    <game name="wheelrom">
      <wheel one="1"/>
    </game>
    <game name="trackballrom">
      <trackball/>
    </game>
  </system>
  <system name="dreamcast">
    <game name="wheelrom">
      <wheel two="2"/>
    </game>
  </system>
  <system name="snes">
    <game name="default">
      <wheel three="3" four="4"/>
    </game>
    <game name="wheelrom">
      <wheel four="42" five="5"/>
    </game>
    <game name="trackballrom">
      <gun foo="bar"/>
    </game>
  </system>
</systems>
""",
    )

    assert getGamesMetaData(system, rom) == snapshot


def test_get_games_meta_data_no_systems(fs: FakeFilesystem) -> None:
    fs.create_file(
        ES_GAMES_METADATA,
        contents="""<?xml version="1.0" encoding="UTF-8"?>
<systems xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="gamesdb.xsd">
</systems>
""",
    )

    assert getGamesMetaData('dreamcast', 'rom one.zip') == {}


@pytest.mark.parametrize(
    'rom',
    [
        'rom one.zip',
        'romTwo.zip',
    ],
)
@pytest.mark.parametrize(
    'system',
    [
        'naomi',
        'naomi2',
        'atomiswave',
        'fbneo',
        'mame',
        'neogeo',
        'triforce',
        'hypseus-singe',
        'model2',
        'model3',
        'hikaru',
        'gaelco',
        'cave3rd',
        'namco2x6',
        'dreamcast',
        'snes',
    ],
)
def test_get_games_meta_data_no_metadata(fs: FakeFilesystem, system: str, rom: str) -> None:
    fs.create_file(
        ES_GAMES_METADATA,
        contents="""<?xml version="1.0" encoding="UTF-8"?>
<systems xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="gamesdb.xsd">
  <system name="arcade">
    <game name="romone">
    </game>
  </system>
  <system name="dreamcast">
    <game name="default"/>
  </system>
</systems>
""",
    )

    assert getGamesMetaData(system, rom) == {}


def test_get_devices_information(mocker: MockerFixture, pyudev: Mock) -> None:
    context_instance = mocker.Mock()

    context_instance.list_devices.return_value = [
        mocker.Mock(device_node='/dev/foo'),
        mocker.Mock(device_node='/dev/input/event0', properties={}),
        mocker.Mock(device_node='/dev/input/event2', properties={'ID_INPUT_TOUCHPAD': '1'}),
        mocker.Mock(device_node='/dev/input/event4', properties={'ID_INPUT_WHEEL': '1'}),
        mocker.Mock(device_node='/dev/input/event3', properties={'ID_INPUT_JOYSTICK': '1', 'ID_PATH': 'foo-bar'}),
        mocker.Mock(device_node='/dev/input/event1', properties={'ID_INPUT_MOUSE': '1'}),
        mocker.Mock(
            device_node='/dev/input/event5',
            properties={'ID_INPUT_JOYSTICK': '1', 'ID_INPUT_WHEEL': '1', 'ID_PATH': 'foo-bar'},
        ),
        mocker.Mock(
            device_node='/dev/input/event6',
            properties={
                'ID_INPUT_JOYSTICK': '1',
                'ID_INPUT_WHEEL': '1',
                'ID_PATH': 'foo-bar-baz',
                'WHEEL_ROTATION_ANGLE': '4',
            },
        ),
    ]

    pyudev.Context.return_value = context_instance

    assert getDevicesInformation() == {
        '/dev/input/event1': {
            'eventId': 1,
            'isJoystick': False,
            'isWheel': False,
            'isMouse': True,
            'associatedDevices': None,
            'joystick_index': None,
            'mouse_index': 0,
        },
        '/dev/input/event2': {
            'eventId': 2,
            'isJoystick': False,
            'isWheel': False,
            'isMouse': True,
            'associatedDevices': None,
            'joystick_index': None,
            'mouse_index': 1,
        },
        '/dev/input/event3': {
            'eventId': 3,
            'isJoystick': True,
            'isWheel': False,
            'isMouse': False,
            'associatedDevices': ['/dev/input/event5'],
            'joystick_index': 0,
            'mouse_index': None,
        },
        '/dev/input/event5': {
            'eventId': 5,
            'isJoystick': True,
            'isWheel': True,
            'isMouse': False,
            'associatedDevices': ['/dev/input/event3'],
            'joystick_index': 1,
            'mouse_index': None,
        },
        '/dev/input/event6': {
            'eventId': 6,
            'isJoystick': True,
            'isWheel': True,
            'isMouse': False,
            'associatedDevices': [],
            'joystick_index': 2,
            'mouse_index': None,
            'wheel_rotation': 4,
        },
    }


def test_get_devices_information_no_devices(mocker: MockerFixture, pyudev: Mock) -> None:
    context_instance = mocker.Mock()

    context_instance.list_devices.return_value = [
        mocker.Mock(device_node='/dev/foo'),
        mocker.Mock(device_node='/dev/input/event0', properties={}),
        mocker.Mock(device_node='/dev/input/event4', properties={'ID_INPUT_WHEEL': '1'}),
    ]

    pyudev.Context.return_value = context_instance

    assert getDevicesInformation() == {}


@pytest.mark.parametrize(
    ('mapping', 'expected'),
    [
        pytest.param({}, None, id='empty mapping'),
        pytest.param({'/dev/input/event0': {}}, None, id='device not in mapping'),
        pytest.param({'/dev/input/event3': {'associatedDevices': None}}, None, id='associatedDevices is None'),
        pytest.param({'/dev/input/event3': {'associatedDevices': []}}, None, id='associatedDevices is empty'),
        pytest.param(
            {
                '/dev/input/event3': {'associatedDevices': ['/dev/input/event1']},
                '/dev/input/event1': {'isMouse': False},
            },
            None,
            id='associated device is not a mouse',
        ),
        pytest.param(
            {
                '/dev/input/event3': {'associatedDevices': ['/dev/input/event1', '/dev/input/event2']},
                '/dev/input/event1': {'isMouse': False},
                '/dev/input/event2': {'isMouse': True},
            },
            '/dev/input/event2',
            id='associated device is a mouse',
        ),
    ],
)
def test_get_associated_mouse(mapping: DeviceInfoMapping, expected: str | None) -> None:
    assert getAssociatedMouse(mapping, '/dev/input/event3') == expected
