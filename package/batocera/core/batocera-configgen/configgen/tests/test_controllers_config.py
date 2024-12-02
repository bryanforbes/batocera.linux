from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ES_GAMES_METADATA
from configgen.controllersConfig import (
    getAssociatedMouse,
    getDevicesInformation,
    getGamesMetaData,
    shortNameFromPath,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.types import DeviceInfoMapping


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
  <system id="arcade">
    <game id="wheelrom">
      <wheel one="1"/>
    </game>
    <game id="trackballrom">
      <trackball/>
    </game>
  </system>
  <system id="dreamcast">
    <game id="wheelrom">
      <wheel two="2"/>
    </game>
  </system>
  <system id="snes">
    <game id="default">
      <wheel three="3" four="4"/>
    </game>
    <game id="wheelrom">
      <wheel four="42" five="5"/>
    </game>
    <game id="trackballrom">
      <gun foo="bar"/>
    </game>
    <game />
  </system>
  <system />
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
  <system id="arcade">
    <game id="romone">
    </game>
  </system>
  <system id="dreamcast">
    <game id="default"/>
  </system>
</systems>
""",
    )

    assert getGamesMetaData(system, rom) == {}


def test_get_devices_information(fs: FakeFilesystem, mocker: MockerFixture, pyudev: Mock) -> None:
    fs.create_file('/sys/devices/event1/actual_device')
    fs.create_symlink('/sys/devices/event1/device/device', link_target='/sys/devices/event1/actual_device')
    fs.create_file('/sys/devices/event2/actual_device')
    fs.create_file('/sys/devices/event3/actual_device')
    fs.create_file('/sys/devices/event5/actual_device')
    fs.create_file('/sys/devices/event6/actual_device')

    context_instance = mocker.Mock()

    context_instance.list_devices.return_value = [
        mocker.Mock(device_node='/dev/foo'),
        mocker.Mock(device_node='/dev/input/event0', properties={}),
        mocker.Mock(
            device_node='/dev/input/event2',
            properties={'ID_INPUT_TOUCHPAD': '1'},
            sys_path='/sys/devices/event2',
        ),
        mocker.Mock(device_node='/dev/input/event4', properties={'ID_INPUT_WHEEL': '1'}),
        mocker.Mock(
            device_node='/dev/input/event3',
            properties={'ID_INPUT_JOYSTICK': '1', 'ID_PATH': 'foo-bar'},
            sys_path='/sys/devices/event3',
        ),
        mocker.Mock(
            device_node='/dev/input/event1', properties={'ID_INPUT_MOUSE': '1'}, sys_path='/sys/devices/event1'
        ),
        mocker.Mock(
            device_node='/dev/input/event5',
            properties={'ID_INPUT_JOYSTICK': '1', 'ID_INPUT_WHEEL': '1', 'ID_PATH': 'foo-bar'},
            sys_path='/sys/devices/event5',
        ),
        mocker.Mock(
            device_node='/dev/input/event6',
            properties={
                'ID_INPUT_JOYSTICK': '1',
                'ID_INPUT_WHEEL': '1',
                'ID_PATH': 'foo-bar-baz',
                'WHEEL_ROTATION_ANGLE': '4',
            },
            sys_path='/sys/devices/event6',
        ),
    ]

    pyudev.Context.return_value = context_instance

    assert getDevicesInformation() == {
        '/dev/input/event1': {
            'eventId': 1,
            'sysfs_path': '/sys/devices/event1/actual_device',
            'isJoystick': False,
            'isWheel': False,
            'isMouse': True,
            'associatedDevices': None,
            'joystick_index': None,
            'mouse_index': 0,
        },
        '/dev/input/event2': {
            'eventId': 2,
            'sysfs_path': '/sys/devices/event2/device/device',
            'isJoystick': False,
            'isWheel': False,
            'isMouse': True,
            'associatedDevices': None,
            'joystick_index': None,
            'mouse_index': 1,
        },
        '/dev/input/event3': {
            'eventId': 3,
            'sysfs_path': '/sys/devices/event3/device/device',
            'isJoystick': True,
            'isWheel': False,
            'isMouse': False,
            'associatedDevices': ['/dev/input/event5'],
            'joystick_index': 0,
            'mouse_index': None,
        },
        '/dev/input/event5': {
            'eventId': 5,
            'sysfs_path': '/sys/devices/event5/device/device',
            'isJoystick': True,
            'isWheel': True,
            'isMouse': False,
            'associatedDevices': ['/dev/input/event3'],
            'joystick_index': 1,
            'mouse_index': None,
        },
        '/dev/input/event6': {
            'eventId': 6,
            'sysfs_path': '/sys/devices/event6/device/device',
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
