from __future__ import annotations

import copy
import re
import signal
from typing import TYPE_CHECKING

import pytest

from configgen.controller import Controller
from configgen.input import Input
from tests.mock_controllers import make_player_controller_dict

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.types import DeviceInfo


def _device_info_from_controller(
    controller: Controller,
    /,
    is_joystick: bool = False,
    is_wheel: bool = False,
    joystick_index: int | None = None,
    wheel_rotation: int | None = None,
) -> DeviceInfo:
    matches = re.match(r'^/dev/input/event([0-9]*)$', controller.device_path)
    info: DeviceInfo = {
        'eventId': -1 if matches is None else int(matches.group(1)),
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
    mock = mocker.Mock()
    mock.readline.return_value = '/dev/input/event40\n'

    os_fdopen.return_value = mock

    return mock


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
    )


def test_reconfigure_controllers(mock_system: Emulator) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    assert reconfigureControllers({}, mock_system, '', {}, {}) == ([], {}, {})


def test_reconfigure_controllers_no_device_info(
    mock_system: Emulator, generic_xbox_pad: Controller, ps3_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = make_player_controller_dict(generic_xbox_pad, ps3_controller)
    expected_controllers = copy.deepcopy(controllers)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {},
        {},
    )

    assert result == (
        [],
        expected_controllers,
        {},
    )
    assert result[1][1] is not controllers[1]
    assert result[1][2] is not controllers[2]


def test_reconfigure_controllers_no_wheels(
    mock_system: Emulator, generic_xbox_pad: Controller, ps3_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = make_player_controller_dict(generic_xbox_pad, ps3_controller)
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1]),
        controllers[2].device_path: _device_info_from_controller(controllers[2]),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )
    assert result[1][1] is not controllers[1]
    assert result[1][2] is not controllers[2]
    assert result[2] is device_info


def test_reconfigure_controllers_player_1_wheel(
    mock_system: Emulator, generic_xbox_pad: Controller, ps3_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = make_player_controller_dict(generic_xbox_pad, ps3_controller)
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
        controllers[2].device_path: _device_info_from_controller(controllers[2]),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )
    assert result[1][1] is not controllers[1]
    assert result[1][2] is not controllers[2]
    assert result[2] is device_info


def test_reconfigure_controllers_player_2_wheel(
    mock_system: Emulator, generic_xbox_pad: Controller, ps3_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = make_player_controller_dict(generic_xbox_pad, ps3_controller)
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1]),
        controllers[2].device_path: _device_info_from_controller(controllers[2], is_wheel=True),
    }
    expected_controllers = {
        1: controllers[2].replace(player_number=1),
        2: controllers[1].replace(player_number=2),
    }
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )
    assert result[1][1] is not controllers[2]
    assert result[1][2] is not controllers[1]
    assert result[2] is device_info


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
def test_reconfigure_controllers_wheel_buttons(
    mock_system: Emulator, mock_controller: Controller, metadata_key: str, metadata_value: str, remapped_key: str
) -> None:
    original_key_mapping = {
        'wheel': 'joystick1left',
        'accelerate': 'r2',
        'brake': 'l2',
        'downshift': 'pageup',
        'upshift': 'pagedown',
    }
    original_key = original_key_mapping[metadata_key]

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    if original_key != remapped_key:
        del expected_controllers[1].inputs[original_key]
        expected_controllers[1].inputs[remapped_key] = mock_controller.inputs[original_key].replace(name=remapped_key)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {f'wheel_{metadata_key}': metadata_value},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


@pytest.mark.system_name('dreamcast')
def test_reconfigure_controllers_wheel_buttons_swap(mock_system: Emulator, mock_controller: Controller) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    expected_controllers[1].inputs['r2'] = mock_controller.inputs['l2'].replace(name='r2')
    expected_controllers[1].inputs['l2'] = mock_controller.inputs['r2'].replace(name='l2')

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_accelerate': 'lt', 'wheel_brake': 'rt'},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


def test_reconfigure_controllers_wheel_buttons_skip_metadata_keys(
    mock_system: Emulator, mock_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'foo_bar': 'a'},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


def test_reconfigure_controllers_wheel_buttons_no_wheel_mapping(
    mock_system: Emulator, mock_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_foo': 'a'},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


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
def test_reconfigure_controllers_wheel_buttons_no_emulator_mapping(
    mock_system: Emulator, mock_controller: Controller, metadata_value: str
) -> None:
    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_accelerate': metadata_value},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


@pytest.mark.system_name('dreamcast')
def test_reconfigure_controllers_wheel_buttons_missing_input(
    mock_system: Emulator, mock_controller: Controller
) -> None:
    del mock_controller.inputs['r2']

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_accelerate': 'rt'},
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


@pytest.mark.parametrize('metadata_rotation', [None, '270'])
@pytest.mark.parametrize('config_rotation', [None, '271'])
@pytest.mark.parametrize('metadata_deadzone', [None, '0'])
@pytest.mark.parametrize('config_deadzone', [None, '0'])
def test_reconfigure_controllers_wheel_rotation_no_reconfigure(
    mock_system: Emulator,
    mock_controller: Controller,
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

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True, wheel_rotation=270),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        metadata,
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


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
def test_reconfigure_controllers_wheel_rotation_no_capabilities(
    mocker: MockerFixture,
    evdev: Mock,
    mock_system: Emulator,
    mock_controller: Controller,
    metadata: dict[str, str],
    capabilities: list[tuple[int, object]],
) -> None:
    mock_input_device = mocker.Mock()
    mock_input_device.capabilities.return_value = {3: capabilities}

    evdev.InputDevice.return_value = mock_input_device

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True, wheel_rotation=270),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        metadata,
        device_info,
    )

    assert result == (
        [],
        expected_controllers,
        expected_device_info,
    )


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
def test_reconfigure_controllers_wheel_rotation(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    rotation: str | None,
    deadzone: str | None,
    midzone: str | None,
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

    subprocess_popen.return_value = mocker.sentinel.popen

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(
            controllers[1], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }
    expected_device_info = copy.deepcopy(device_info)
    expected_controllers = copy.deepcopy(controllers)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        metadata,
        device_info,
    )

    assert result == (
        [mocker.sentinel.popen],
        {
            1: expected_controllers[1].replace(
                device_path='/dev/input/event40',
                index=1,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            )
        },
        {
            **expected_device_info,
            '/dev/input/event40': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 1,
            },
        },
    )

    os_fdopen.assert_called_once_with(mocker.sentinel.pipeout)
    mock_fd.close.assert_called_once_with()
    os_kill.assert_not_called()

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
@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd', 'os_kill')
def test_reconfigure_controllers_wheel_rotation_config_override(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    rotation: str | None,
    deadzone: str | None,
    midzone: str | None,
    subprocess_popen: Mock,
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

    subprocess_popen.return_value = mocker.sentinel.popen

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(
            controllers[1], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }
    expected_device_info = copy.deepcopy(device_info)
    expected_controllers = copy.deepcopy(controllers)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        metadata,
        device_info,
    )

    assert result == (
        [mocker.sentinel.popen],
        {
            1: expected_controllers[1].replace(
                device_path='/dev/input/event40',
                index=1,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            )
        },
        {
            **expected_device_info,
            '/dev/input/event40': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 1,
            },
        },
    )

    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe')
def test_reconfigure_controllers_wheel_rotation_two_controllers(
    mocker: MockerFixture,
    evdev: Mock,
    mock_system: Emulator,
    mock_controller: Controller,
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
    subprocess_popen.side_effect = [mocker.sentinel.popen1, mocker.sentinel.popen2]

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {
        1: mock_controller,
        2: mock_controller.replace(player_number=2, index=1, device_path='/dev/input/event2'),
    }
    device_info = {
        controllers[1].device_path: _device_info_from_controller(
            controllers[1], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
        controllers[2].device_path: _device_info_from_controller(
            controllers[2], is_wheel=True, wheel_rotation=360, is_joystick=True, joystick_index=1
        ),
    }
    expected_controllers = copy.deepcopy(controllers)
    expected_device_info = copy.deepcopy(device_info)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_rotation': '260'},
        device_info,
    )

    assert result == (
        [mocker.sentinel.popen1, mocker.sentinel.popen2],
        {
            1: expected_controllers[1].replace(
                device_path='/dev/input/event20',
                index=2,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            ),
            2: expected_controllers[2].replace(
                device_path='/dev/input/event21',
                index=3,
                physical_device_path='/dev/input/event2',
                physical_index=1,
            ),
        },
        {
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
        },
    )

    os_kill.assert_not_called()

    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe', 'mock_fd', 'os_kill')
def test_reconfigure_controllers_recompute_ids(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    subprocess_popen: Mock,
) -> None:
    subprocess_popen.side_effect = [mocker.sentinel.popen1, mocker.sentinel.popen2]

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {
        1: mock_controller,
        2: mock_controller.replace(player_number=2, index=1, device_path='/dev/input/event4'),
        3: mock_controller.replace(player_number=3, index=2, device_path='/dev/input/something5'),
    }
    device_info = {
        controllers[1].device_path: _device_info_from_controller(
            controllers[1], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
        '/dev/input/event2': {'isJoystick': False, 'eventId': 2},
        '/dev/input/event3': {'isJoystick': True, 'eventId': 3},
        controllers[2].device_path: _device_info_from_controller(controllers[2], is_joystick=True, joystick_index=3),
    }
    expected_device_info = copy.deepcopy(device_info)
    expected_controllers = copy.deepcopy(controllers)

    result = reconfigureControllers(
        controllers,
        mock_system,
        '',
        {'wheel_rotation': '260'},
        device_info,
    )

    assert result == (
        [mocker.sentinel.popen1],
        {
            1: expected_controllers[1].replace(
                device_path='/dev/input/event40',
                index=3,
                physical_device_path='/dev/input/event1',
                physical_index=0,
            ),
            2: expected_controllers[2].replace(index=2),
            3: expected_controllers[3],
        },
        {
            **expected_device_info,
            '/dev/input/event4': {
                **expected_device_info['/dev/input/event4'],
                'joystick_index': 2,
            },
            '/dev/input/event40': {
                **expected_device_info['/dev/input/event1'],
                'eventId': 40,
                'joystick_index': 3,
            },
        },
    )


@pytest.mark.usefixtures('mock_controller_capabilities', 'os_pipe')
def test_reconfigure_controllers_raises(
    mocker: MockerFixture,
    mock_system: Emulator,
    mock_controller: Controller,
    subprocess_popen: Mock,
    os_fdopen: Mock,
    os_kill: Mock,
) -> None:
    mock_system.config['wheel_rotation'] = '260'
    os_fdopen.side_effect = Exception('Test exception')

    mock_popen = mocker.Mock()
    mock_popen.pid = mocker.sentinel.popen_pid
    mock_popen.communicate.return_value = (b'', b'')
    subprocess_popen.return_value = mock_popen

    from configgen.utils.wheelsUtils import reconfigureControllers

    controllers = {1: mock_controller}
    device_info = {
        controllers[1].device_path: _device_info_from_controller(
            controllers[1], is_wheel=True, wheel_rotation=270, is_joystick=True, joystick_index=0
        ),
    }

    with pytest.raises(Exception, match='^Test exception$'):
        reconfigureControllers(
            controllers,
            mock_system,
            '',
            {},
            device_info,
        )

    os_kill.assert_called_once_with(mocker.sentinel.popen_pid, signal.SIGTERM)
    mock_popen.communicate.assert_called_once_with()


def test_get_wheels_from_devices_infos(
    generic_xbox_pad: Controller, ps3_controller: Controller, keyboard_controller: Controller
) -> None:
    from configgen.utils.wheelsUtils import getWheelsFromDevicesInfos

    controllers = make_player_controller_dict(generic_xbox_pad, ps3_controller, keyboard_controller)
    device_infos = {
        controllers[1].device_path: _device_info_from_controller(controllers[1], is_wheel=True),
        controllers[2].device_path: _device_info_from_controller(controllers[2]),
        controllers[3].device_path: _device_info_from_controller(controllers[3], is_wheel=True),
    }
    assert getWheelsFromDevicesInfos(device_infos) == {
        controllers[1].device_path: device_infos[controllers[1].device_path],
        controllers[3].device_path: device_infos[controllers[3].device_path],
    }


def test_reset_controllers(mocker: MockerFixture, os_kill: Mock) -> None:
    from configgen.utils.wheelsUtils import resetControllers

    mock_popen_1 = mocker.Mock(pid=mocker.sentinel.mock_popen_1_pid)
    mock_popen_2 = mocker.Mock(pid=mocker.sentinel.mock_popen_2_pid)
    mock_popen_1.communicate.return_value = (b'', b'')
    mock_popen_2.communicate.return_value = (b'', b'')

    resetControllers([mock_popen_1, mock_popen_2])

    assert os_kill.call_args_list == [
        mocker.call(mocker.sentinel.mock_popen_1_pid, signal.SIGTERM),
        mocker.call(mocker.sentinel.mock_popen_2_pid, signal.SIGTERM),
    ]
    mock_popen_1.communicate.assert_called_once_with()
    mock_popen_2.communicate.assert_called_once_with()
