from __future__ import annotations

import copy
import re
import signal
from typing import TYPE_CHECKING, cast

import pytest

from configgen.controller import Controller
from configgen.input import Input
from configgen.utils.wheelsUtils import configure_wheels
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.types import DeviceInfo


pytestmark = pytest.mark.mock_system_config({'use_wheels': '1'})


def _device_info_from_controller(
    controller: Controller,
    /,
    is_joystick: bool = False,
    is_wheel: bool = False,
    joystick_index: int | None = None,
    wheel_rotation: int | None = None,
) -> DeviceInfo:
    matches = re.match(r'^/dev/input/event([0-9]*)$', controller.device_path)
    id = -1 if matches is None else int(matches.group(1))
    info: DeviceInfo = {
        'eventId': id,
        'sysfs_path': f'/sys/devices/event{id}/actual_device',
        'isJoystick': is_joystick,
        'isWheel': is_wheel,
        'isMouse': False,
        'joystick_index': joystick_index,
        'mouse_index': None,
        'associatedDevices': None,
    }

    if wheel_rotation is not None:
        info['wheel_rotation'] = wheel_rotation

    return info


@pytest.fixture(autouse=True)
def evdev(evdev: Mock) -> Mock:
    evdev.ecodes.EV_ABS = 3
    return evdev


@pytest.fixture(autouse=True)
def subprocess_popen(mocker: MockerFixture, subprocess_popen: Mock) -> Mock:
    mock_popen = mocker.Mock()
    mock_popen.pid = mocker.sentinel.popen_pid

    subprocess_popen.return_value = mock_popen

    return subprocess_popen


@pytest.fixture
def mock_controller_capabilities(mocker: MockerFixture, evdev: Mock) -> Mock:
    mock_input_device = mocker.Mock()
    mock_input_device.capabilities.return_value = {
        3: [(0, mocker.Mock(min=-180, max=180))],
    }

    evdev.InputDevice.return_value = mock_input_device

    return evdev


@pytest.fixture
def emulator() -> str:
    return 'mock'


@pytest.fixture(autouse=True)
def os_access(mocker: MockerFixture) -> Mock:
    return mocker.patch('os.access', return_value=False)


@pytest.fixture
def os_kill(mocker: MockerFixture) -> Mock:
    return mocker.patch('os.kill')


@pytest.fixture
def os_pipe(mocker: MockerFixture) -> Mock:
    return mocker.patch('os.pipe', return_value=(mocker.sentinel.pipeout, mocker.sentinel.pipein))


@pytest.fixture
def os_fdopen(mocker: MockerFixture) -> Mock:
    return mocker.patch('os.fdopen')


@pytest.fixture
def mock_fd(mocker: MockerFixture, os_fdopen: Mock) -> Mock:
    mock = mocker.MagicMock()
    mock.readline.return_value = '/dev/input/event40\n'
    mock.__enter__.return_value = mock

    os_fdopen.return_value = mock

    return mock


@pytest.fixture(autouse=True)
def get_devices_information(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.controllersConfig.getDevicesInformation', return_value={})


@pytest.fixture
def mock_controller() -> Controller:
    return Controller(
        name='Mock controller',
        type='joystick',
        guid='0',
        real_name='Mock controller real_name',
        device_path='/dev/input/event1',
        player_number=1,
        index=0,
        inputs_={
            input.name: input
            for input in [
                Input(name='r2', type='button', id='0', value='1', code='313'),
                Input(name='l2', type='button', id='1', value='1', code='314'),
                Input(name='pageup', type='button', id='2', value='1', code='315'),
                Input(name='pagedown', type='button', id='3', value='1', code='316'),
                Input(name='a', type='button', id='4', value='1', code='317'),
                Input(name='b', type='button', id='5', value='1', code='318'),
                Input(name='x', type='button', id='6', value='1', code='319'),
                Input(name='y', type='button', id='7', value='1', code='320'),
                Input(name='start', type='button', id='8', value='1', code='321'),
                Input(name='select', type='button', id='9', value='1', code='322'),
                Input(name='joystick1left', type='axis', id='0', value='-1', code='0'),
            ]
        },
        button_count=10,
        axis_count=1,
        hat_count=0,
    )


@pytest.mark.mock_system_config({'use_wheels': '0'})
def test_configure_wheels(
    mock_system: Emulator,
    generic_xbox_pad: Controller,
    ps3_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
) -> None:
    controllers = make_player_controller_list(generic_xbox_pad, ps3_controller)
    expected_controllers = copy.deepcopy(controllers)

    with configure_wheels(controllers, mock_system, {}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == {}

    get_devices_information.assert_not_called()
    os_kill.assert_not_called()


def test_configure_wheels_no_controllers(mock_system: Emulator, get_devices_information: Mock, os_kill: Mock) -> None:
    with configure_wheels([], mock_system, {}) as (controllers, wheels):
        assert controllers == []
        assert wheels == {}

    get_devices_information.assert_not_called()
    os_kill.assert_not_called()


def test_configure_wheels_no_device_info(
    mock_system: Emulator, generic_xbox_pad: Controller, ps3_controller: Controller, os_kill: Mock
) -> None:
    original_controllers = make_player_controller_list(generic_xbox_pad, ps3_controller)
    expected_controllers = copy.deepcopy(original_controllers)

    with configure_wheels(original_controllers, mock_system, {}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == {}

    assert controllers[0] is not original_controllers[0]
    assert controllers[1] is not original_controllers[1]

    os_kill.assert_not_called()


def test_configure_wheels_no_wheels(
    mock_system: Emulator,
    generic_xbox_pad: Controller,
    ps3_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
) -> None:
    original_controllers = make_player_controller_list(generic_xbox_pad, ps3_controller)
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0]),
        original_controllers[1].device_path: _device_info_from_controller(original_controllers[1]),
    }
    expected_controllers = copy.deepcopy(original_controllers)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == {}

    assert controllers[0] is not original_controllers[0]
    assert controllers[1] is not original_controllers[1]

    os_kill.assert_not_called()


def test_configure_wheels_player_1_wheel(
    mock_system: Emulator,
    g920_wheel: Controller,
    ps3_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
) -> None:
    original_controllers = make_player_controller_list(g920_wheel, ps3_controller)
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
        original_controllers[1].device_path: _device_info_from_controller(original_controllers[1]),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = {
        original_controllers[0].device_path: copy.deepcopy(device_info[original_controllers[0].device_path])
    }

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    assert controllers[0] is not original_controllers[0]
    assert controllers[1] is not original_controllers[1]

    os_kill.assert_not_called()


def test_configure_wheels_player_2_wheel(
    mock_system: Emulator,
    g920_wheel: Controller,
    ps3_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
) -> None:
    original_controllers = make_player_controller_list(ps3_controller, g920_wheel)
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0]),
        original_controllers[1].device_path: _device_info_from_controller(original_controllers[1], is_wheel=True),
    }
    expected_controllers = [
        original_controllers[1].replace(player_number=1),
        original_controllers[0].replace(player_number=2),
    ]
    expected_wheels = {
        original_controllers[1].device_path: copy.deepcopy(device_info[original_controllers[1].device_path])
    }

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    assert controllers[0] is not original_controllers[1]
    assert controllers[1] is not original_controllers[0]

    os_kill.assert_not_called()


@pytest.mark.parametrize(
    ('system_name', 'metadata_key', 'metadata_value', 'remapped_key'),
    [
        ('dreamcast', 'accelerate', 'rt', 'r2'),
        ('dreamcast', 'brake', 'lt', 'l2'),
        ('dreamcast', 'downshift', 'down', 'pagedown'),
        ('dreamcast', 'upshift', 'up', 'pageup'),
        ('dreamcast', 'wheel', 'rt', 'r2'),
        ('gamecube', 'accelerate', 'rt', 'r2'),
        ('gamecube', 'brake', 'lt', 'l2'),
        ('gamecube', 'downshift', 'a', 'a'),
        ('gamecube', 'upshift', 'b', 'b'),
        ('gamecube', 'upshift', 'x', 'x'),
        ('gamecube', 'upshift', 'y', 'y'),
        ('gamecube', 'wheel', 'y', 'y'),
        ('saturn', 'accelerate', 'b', 'a'),
        ('saturn', 'brake', 'a', 'b'),
        ('saturn', 'downshift', 'l', 'l2'),
        ('saturn', 'upshift', 'r', 'r2'),
        ('saturn', 'accelerate', 'c', 'pagedown'),
        ('saturn', 'accelerate', 'x', 'y'),
        ('saturn', 'accelerate', 'y', 'x'),
        ('saturn', 'accelerate', 'z', 'pageup'),
        ('saturn', 'accelerate', 'start', 'start'),
        ('saturn', 'wheel', 'start', 'start'),
        ('n64', 'accelerate', 'a', 'b'),
        ('n64', 'brake', 'b', 'y'),
        ('n64', 'downshift', 'l', 'pageup'),
        ('n64', 'upshift', 'r', 'pagedown'),
        ('n64', 'accelerate', 'start', 'start'),
        ('n64', 'wheel', 'start', 'start'),
        ('wii', 'accelerate', 'a', 'a'),
        ('wii', 'brake', 'b', 'b'),
        ('wii', 'downshift', 'lt', 'l2'),
        ('wii', 'upshift', 'rt', 'r2'),
        ('wii', 'upshift', 'x', 'x'),
        ('wii', 'upshift', 'y', 'y'),
        ('wii', 'wheel', 'y', 'y'),
        ('wiiu', 'accelerate', 'a', 'a'),
        ('wiiu', 'brake', 'b', 'b'),
        ('wiiu', 'upshift', 'x', 'x'),
        ('wiiu', 'downshift', 'y', 'y'),
        ('wiiu', 'downshift', 'start', 'start'),
        ('wiiu', 'downshift', 'select', 'select'),
        ('wiiu', 'wheel', 'select', 'select'),
        ('psx', 'accelerate', 'cross', 'b'),
        ('psx', 'brake', 'square', 'y'),
        ('psx', 'upshift', 'round', 'a'),
        ('psx', 'downshift', 'triangle', 'x'),
        ('psx', 'downshift', 'start', 'start'),
        ('psx', 'downshift', 'select', 'select'),
        ('psx', 'wheel', 'select', 'select'),
        ('ps2', 'accelerate', 'cross', 'b'),
        ('ps2', 'brake', 'square', 'y'),
        ('ps2', 'upshift', 'round', 'a'),
        ('ps2', 'downshift', 'triangle', 'x'),
        ('ps2', 'wheel', 'triangle', 'x'),
        ('xbox', 'accelerate', 'lt', 'l2'),
        ('xbox', 'brake', 'rt', 'r2'),
        ('xbox', 'upshift', 'a', 'b'),
        ('xbox', 'downshift', 'b', 'a'),
        ('xbox', 'downshift', 'x', 'y'),
        ('xbox', 'downshift', 'y', 'x'),
        ('xbox', 'wheel', 'y', 'x'),
    ],
)
def test_configure_wheels_wheel_buttons(
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    metadata_key: str,
    metadata_value: str,
    remapped_key: str,
    os_kill: Mock,
) -> None:
    original_key_mapping = {
        'wheel': 'joystick1left',
        'accelerate': 'r2',
        'brake': 'l2',
        'downshift': 'pageup',
        'upshift': 'pagedown',
    }
    original_key = original_key_mapping[metadata_key]

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    if original_key != remapped_key:
        del expected_controllers[0].inputs[original_key]
        expected_controllers[0].inputs[remapped_key] = mock_controller.inputs[original_key].replace(name=remapped_key)

    with configure_wheels(original_controllers, mock_system, {f'wheel_{metadata_key}': metadata_value}) as (
        controllers,
        wheels,
    ):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.system_name('dreamcast')
def test_configure_wheels_buttons_swap(
    mock_system: Emulator, mock_controller: Controller, get_devices_information: Mock, os_kill: Mock
) -> None:
    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    expected_controllers[0].inputs['r2'] = mock_controller.inputs['l2'].replace(name='r2')
    expected_controllers[0].inputs['l2'] = mock_controller.inputs['r2'].replace(name='l2')

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_accelerate': 'lt', 'wheel_brake': 'rt'}) as (
        controllers,
        wheels,
    ):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


def test_configure_wheels_skip_metadata_keys(
    mock_system: Emulator, mock_controller: Controller, get_devices_information: Mock, os_kill: Mock
) -> None:
    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'foo_bar': 'a'}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


def test_configure_wheels_no_wheel_mapping(
    mock_system: Emulator, mock_controller: Controller, get_devices_information: Mock, os_kill: Mock
) -> None:
    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_foo': 'a'}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.parametrize(
    ('system_name', 'metadata_value'),
    [
        ('unset', 'lt'),
        ('dreamcast', 'select'),
        ('gamecube', 'select'),
        ('saturn', 'select'),
        ('n64', 'select'),
        ('wii', 'select'),
        ('wiiu', 'lt'),
        ('psx', 'lt'),
        ('ps2', 'select'),
        ('xbox', 'select'),
    ],
)
def test_configure_wheels_no_emulator_mapping(
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    metadata_value: str,
    os_kill: Mock,
) -> None:
    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_accelerate': metadata_value}) as (
        controllers,
        wheels,
    ):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.system_name('dreamcast')
def test_configure_wheels_missing_input(
    mock_system: Emulator, mock_controller: Controller, get_devices_information: Mock, os_kill: Mock
) -> None:
    del mock_controller.inputs['r2']

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(original_controllers[0], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_accelerate': 'rt'}) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.parametrize('metadata_rotation', [None, '270'])
@pytest.mark.parametrize('config_rotation', [None, '271'])
@pytest.mark.parametrize('metadata_deadzone', [None, '0'])
@pytest.mark.parametrize('config_deadzone', [None, '0'])
def test_configure_wheels_no_reconfigure(
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
    config_deadzone: str | None,
    metadata_deadzone: str | None,
    config_rotation: str | None,
    metadata_rotation: str | None,
) -> None:
    if config_deadzone:
        mock_system.config['wheel_deadzone'] = config_deadzone
    if config_rotation:
        mock_system.config['wheel_rotation'] = config_rotation

    metadata: dict[str, str] = {}

    if metadata_deadzone:
        metadata['wheel_deadzone'] = metadata_deadzone
    if metadata_rotation:
        metadata['wheel_rotation'] = metadata_rotation

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270
        ),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, metadata) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.parametrize('capabilities', [[], [(99, object())]], ids=['empty abs list', 'no matching abs entries'])
@pytest.mark.parametrize(
    ('mock_system_config', 'metadata'),
    [
        pytest.param({'wheel_rotation': '269'}, {}, id='config wheel rotation'),
        pytest.param({'wheel_deadzone': '1'}, {}, id='config wheel deadzone'),
        pytest.param({}, {'wheel_rotation': '269'}, id='metadata wheel rotation'),
        pytest.param({}, {'wheel_deadzone': '1'}, id='metadata wheel deadzone'),
    ],
)
def test_configure_wheels_no_capabilities(
    mocker: MockerFixture,
    evdev: Mock,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    os_kill: Mock,
    metadata: dict[str, str],
    capabilities: list[tuple[int, object]],
) -> None:
    mock_input_device = mocker.Mock()
    mock_input_device.capabilities.return_value = {3: capabilities}

    evdev.InputDevice.return_value = mock_input_device

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270
        ),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, metadata) as (controllers, wheels):
        assert controllers == expected_controllers
        assert wheels == expected_wheels

    os_kill.assert_not_called()


@pytest.mark.parametrize(
    ('rotation', 'deadzone', 'midzone'),
    [
        pytest.param('260', None, None),
        pytest.param('260', '1', None),
        pytest.param('260', '2', None),
        pytest.param('260', '1', '1'),
        pytest.param('260', '1', '2'),
        pytest.param('260', '2', '2'),
        pytest.param('260', '3', '2'),
        pytest.param('260', '4', '2'),
        pytest.param(None, '1', None),
        pytest.param(None, '2', None),
        pytest.param(None, '1', '1'),
        pytest.param(None, '1', '2'),
        pytest.param(None, '2', '2'),
        pytest.param(None, '3', '2'),
        pytest.param(None, '4', '2'),
    ],
)
@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe')
def test_configure_wheels_wheel_rotation(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    rotation: str | None,
    deadzone: str | None,
    midzone: str | None,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    mock_fd: Mock,
    os_fdopen: Mock,
    os_kill: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    metadata: dict[str, str] = {}

    if rotation:
        metadata['wheel_rotation'] = rotation
    if deadzone:
        metadata['wheel_deadzone'] = deadzone
    if midzone:
        metadata['wheel_midzone'] = midzone

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_wheels = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, metadata) as (controllers, wheels):
        assert controllers == [
            expected_controllers[0].replace(
                guid='03000000010000000100000001000000',
                device_path='/dev/input/event40',
                index=1,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            )
        ]
        assert wheels == {
            **expected_wheels,
            '/dev/input/event40': {
                **expected_wheels['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 1,
            },
        }
        os_kill.assert_not_called()

    os_fdopen.assert_called_once_with(mocker.sentinel.pipeout)
    mock_fd.__exit__.assert_called_once_with(None, None, None)
    os_kill.assert_called_once_with(mocker.sentinel.popen_pid, signal.SIGTERM)
    subprocess_popen.return_value.communicate.assert_called_once_with()
    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.parametrize(
    ('rotation', 'deadzone', 'midzone'),
    [
        pytest.param('260', None, None),
        pytest.param('260', '1', None),
        pytest.param('260', '2', None),
        pytest.param('260', '1', '1'),
        pytest.param('260', '1', '2'),
        pytest.param('260', '2', '2'),
        pytest.param('260', '3', '2'),
        pytest.param('260', '4', '2'),
        pytest.param(None, '1', None),
        pytest.param(None, '2', None),
        pytest.param(None, '1', '1'),
        pytest.param(None, '1', '2'),
        pytest.param(None, '2', '2'),
        pytest.param(None, '3', '2'),
        pytest.param(None, '4', '2'),
    ],
)
@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd')
def test_configure_wheels_wheel_rotation_config_override(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    rotation: str | None,
    deadzone: str | None,
    midzone: str | None,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    os_kill: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    metadata: dict[str, str] = {}

    if rotation:
        metadata['wheel_rotation'] = rotation
        mock_system.config['wheel_rotation'] = rotation
    if deadzone:
        metadata['wheel_deadzone'] = '8'
        mock_system.config['wheel_deadzone'] = deadzone
    if midzone:
        metadata['wheel_midzone'] = '8'
        mock_system.config['wheel_midzone'] = midzone

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }
    expected_device_info = copy.deepcopy(device_info)
    expected_controllers = copy.deepcopy(original_controllers)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, metadata) as (controllers, wheels):
        assert controllers == [
            expected_controllers[0].replace(
                guid='03000000010000000100000001000000',
                device_path='/dev/input/event40',
                index=1,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            )
        ]
        assert wheels == {
            **expected_device_info,
            '/dev/input/event40': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 1,
            },
        }
        os_kill.assert_not_called()

    os_kill.assert_called_once_with(mocker.sentinel.popen_pid, signal.SIGTERM)

    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe')
def test_configure_wheels_wheel_rotation_two_controllers(
    mocker: MockerFixture,
    evdev: Mock,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    mock_fd: Mock,
    os_kill: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    mock_input_device_1 = mocker.Mock()
    mock_input_device_1.capabilities.return_value = {
        3: [(0, mocker.Mock(min=-180, max=180))],
    }
    mock_input_device_2 = mocker.Mock()
    mock_input_device_2.capabilities.return_value = {
        3: [(0, mocker.Mock(min=-270, max=270))],
    }

    mock_fd.readline.side_effect = ['/dev/input/event20', '/dev/input/event21']
    evdev.InputDevice.side_effect = [mock_input_device_1, mock_input_device_2]

    mock_popen1 = mocker.Mock()
    mock_popen1.pid = mocker.sentinel.pid1
    mock_popen2 = mocker.Mock()
    mock_popen2.pid = mocker.sentinel.pid2

    subprocess_popen.side_effect = [mock_popen1, mock_popen2]

    original_controllers = [
        mock_controller,
        mock_controller.replace(player_number=2, index=1, device_path='/dev/input/event2'),
    ]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
        original_controllers[1].device_path: _device_info_from_controller(
            original_controllers[1], is_wheel=True, wheel_rotation=360, is_joystick=True, joystick_index=1
        ),
    }
    expected_controllers = copy.deepcopy(original_controllers)
    expected_device_info = copy.deepcopy(device_info)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_rotation': '260'}) as (controllers, wheels):
        assert controllers == [
            expected_controllers[0].replace(
                guid='03000000010000000100000001000000',
                device_path='/dev/input/event20',
                index=2,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            ),
            expected_controllers[1].replace(
                guid='03000000010000000100000001000000',
                device_path='/dev/input/event21',
                index=3,
                physical_device_path='/dev/input/event2',
                physical_index=1,
            ),
        ]
        assert wheels == {
            **expected_device_info,
            '/dev/input/event20': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 20,
                'joystick_index': 2,
            },
            '/dev/input/event21': {
                **expected_device_info['/dev/input/event2'],
                'eventId': 21,
                'joystick_index': 3,
            },
        }
        os_kill.assert_not_called()

    assert os_kill.call_args_list == [
        mocker.call(mocker.sentinel.pid1, signal.SIGTERM),
        mocker.call(mocker.sentinel.pid2, signal.SIGTERM),
    ]

    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd')
def test_configure_wheels_recompute_ids(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    os_kill: Mock,
) -> None:
    mock_popen1 = mocker.Mock()
    mock_popen1.pid = mocker.sentinel.pid1
    mock_popen2 = mocker.Mock()
    mock_popen2.pid = mocker.sentinel.pid2
    mock_popen3 = mocker.Mock()
    mock_popen3.pid = mocker.sentinel.pid3

    subprocess_popen.side_effect = [mock_popen1, mock_popen2, mock_popen3]

    original_controllers = [
        mock_controller,
        mock_controller.replace(player_number=2, index=1, device_path='/dev/input/event4'),
        mock_controller.replace(player_number=3, index=2, device_path='/dev/input/something5'),
    ]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
        '/dev/input/event2': cast('DeviceInfo', {'isWheel': False, 'isJoystick': False, 'eventId': 2}),
        '/dev/input/event3': cast('DeviceInfo', {'isWheel': False, 'isJoystick': True, 'eventId': 3}),
        original_controllers[1].device_path: _device_info_from_controller(
            original_controllers[1], is_joystick=True, joystick_index=3
        ),
    }
    expected_device_info = copy.deepcopy(device_info)
    expected_controllers = copy.deepcopy(original_controllers)

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {'wheel_rotation': '260'}) as (controllers, wheels):
        assert controllers == [
            expected_controllers[0].replace(
                guid='03000000010000000100000001000000',
                device_path='/dev/input/event40',
                index=3,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            ),
            expected_controllers[1].replace(index=2),
            expected_controllers[2],
        ]
        assert wheels == {
            '/dev/input/event1': expected_device_info['/dev/input/event1'],
            '/dev/input/event40': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 3,
            },
        }
        os_kill.assert_not_called()

    os_kill.assert_called_once_with(mocker.sentinel.pid1, signal.SIGTERM)


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe')
def test_configure_wheels_raises(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    os_kill: Mock,
    mock_fd: Mock,
) -> None:
    mock_system.config['wheel_rotation'] = '260'
    test_exception = Exception('Test exception')
    mock_fd.readline.side_effect = test_exception

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }

    get_devices_information.return_value = device_info

    with (
        pytest.raises(Exception, match=r'^Test exception$'),
        configure_wheels(original_controllers, mock_system, {}) as _,
    ):
        ...

    mock_fd.__exit__.assert_called_once_with(Exception, test_exception, mocker.ANY)
    os_kill.assert_called_once_with(mocker.sentinel.popen_pid, signal.SIGTERM)
    subprocess_popen.return_value.communicate.assert_called_once_with()


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd')
def test_configure_wheels_context_cleanup(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    os_kill: Mock,
) -> None:
    mock_system.config['wheel_rotation'] = '260'
    test_exception = Exception('Test exception')

    mock_popen = mocker.Mock()
    mock_popen.pid = mocker.sentinel.popen_pid
    subprocess_popen.return_value = mock_popen

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }

    get_devices_information.return_value = device_info

    with (  # noqa: PT012
        pytest.raises(Exception, match=r'^Test exception$'),
        configure_wheels(original_controllers, mock_system, {}) as _,
    ):
        os_kill.assert_not_called()
        raise test_exception

    os_kill.assert_called_once_with(mocker.sentinel.popen_pid, signal.SIGTERM)
    mock_popen.communicate.assert_called_once_with()


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd')
def test_configure_wheels_context_cleanup_fails(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    get_devices_information: Mock,
    subprocess_popen: Mock,
    os_kill: Mock,
) -> None:
    mock_system.config['wheel_rotation'] = '260'
    test_exception = Exception('Test exception')
    os_kill.side_effect = test_exception

    mock_popen = mocker.Mock()
    mock_popen.pid = mocker.sentinel.popen_pid
    subprocess_popen.return_value = mock_popen

    original_controllers = [mock_controller]
    device_info = {
        original_controllers[0].device_path: _device_info_from_controller(
            original_controllers[0], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }

    get_devices_information.return_value = device_info

    with configure_wheels(original_controllers, mock_system, {}) as _:
        ...
