from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

import pytest

from configgen.controller import Controller, ControllerMapping
from configgen.input import Input

if TYPE_CHECKING:
    from collections.abc import Mapping
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'no_fs_mods: do not modify the fake filesystem')
    config.addinivalue_line('markers', 'system_name(name): the system name to set the test to use')
    config.addinivalue_line('markers', 'core(name): the core to set the test to use')
    config.addinivalue_line('markers', 'mock_system_config(config): the mock system config to use')


@pytest.fixture
def generic_xbox_pad() -> Controller:
    root = ET.fromstring("""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="Generic Xbox pad" deviceGUID="030000005e0400000a0b000005040000">
		<input name="a" type="button" id="0" value="1" code="304" />
		<input name="b" type="button" id="1" value="1" code="305" />
		<input name="down" type="hat" id="0" value="4" code="16" />
		<input name="hotkey" type="button" id="8" value="1" code="314" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="2" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="3" value="-1" code="4" />
		<input name="l2" type="button" id="6" value="1" code="312" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="hat" id="0" value="8" code="16" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="button" id="7" value="1" code="313" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="hat" id="0" value="2" code="16" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="hat" id="0" value="1" code="16" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
</inputList>""")

    return Controller(
        name='Generic Xbox pad',
        type='joystick',
        guid='030000005e0400000a0b000005040000',
        player_number=-1,
        index=-1,
        real_name='',
        device_path='',
        button_count=13,
        axis_count=4,
        hat_count=4,
        inputs_=Input.from_parent_element(cast(ET.Element, root.find('./inputConfig'))),
    )


@pytest.fixture
def gpio_controller_1() -> Controller:
    root = ET.fromstring("""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="GPIO Controller 1" deviceGUID="15000000010000000100000000010000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="axis" id="1" value="1" code="1" />
		<input name="hotkey" type="button" id="8" value="1" code="316" />
		<input name="left" type="axis" id="0" value="-1" code="0" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="right" type="axis" id="0" value="1" code="0" />
		<input name="select" type="button" id="6" value="1" code="314" />
		<input name="start" type="button" id="7" value="1" code="315" />
		<input name="up" type="axis" id="1" value="-1" code="1" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
</inputList>""")

    return Controller(
        name='GPIO Controller 1',
        type='joystick',
        guid='15000000010000000100000000010000',
        player_number=-1,
        index=-1,
        real_name='',
        device_path='',
        button_count=9,
        axis_count=4,
        hat_count=0,
        inputs_=Input.from_parent_element(cast(ET.Element, root.find('./inputConfig'))),
    )


@pytest.fixture
def ps3_controller() -> Controller:
    root = ET.fromstring("""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="Sony PLAYSTATION(R)3 Controller" deviceGUID="030000004c0500006802000011810000">
		<input name="a" type="button" id="1" value="1" code="305" />
		<input name="b" type="button" id="0" value="1" code="304" />
		<input name="down" type="button" id="14" value="1" code="545" />
		<input name="hotkey" type="button" id="10" value="1" code="316" />
		<input name="joystick1left" type="axis" id="0" value="-1" code="0" />
		<input name="joystick1up" type="axis" id="1" value="-1" code="1" />
		<input name="joystick2left" type="axis" id="3" value="-1" code="3" />
		<input name="joystick2up" type="axis" id="4" value="-1" code="4" />
		<input name="l2" type="axis" id="2" value="1" code="2" />
		<input name="l3" type="button" id="11" value="1" code="317" />
		<input name="left" type="button" id="15" value="1" code="546" />
		<input name="pagedown" type="button" id="5" value="1" code="311" />
		<input name="pageup" type="button" id="4" value="1" code="310" />
		<input name="r2" type="axis" id="5" value="1" code="5" />
		<input name="r3" type="button" id="12" value="1" code="318" />
		<input name="right" type="button" id="16" value="1" code="547" />
		<input name="select" type="button" id="8" value="1" code="314" />
		<input name="start" type="button" id="9" value="1" code="315" />
		<input name="up" type="button" id="13" value="1" code="544" />
		<input name="x" type="button" id="2" value="1" code="307" />
		<input name="y" type="button" id="3" value="1" code="308" />
	</inputConfig>
</inputList>""")

    return Controller(
        name='Sony PLAYSTATION(R)3 Controller',
        type='joystick',
        guid='030000004c0500006802000011810000',
        player_number=-1,
        index=-1,
        real_name='',
        device_path='',
        button_count=15,
        axis_count=6,
        hat_count=0,
        inputs_=Input.from_parent_element(cast(ET.Element, root.find('./inputConfig'))),
    )


@pytest.fixture
def keyboard_controller() -> Controller:
    root = ET.fromstring("""<?xml version="1.0"?>
<inputList>
	<inputConfig type="keyboard" deviceName="Keyboard" deviceGUID="-1">
		<input name="up" type="key" id="1073741906" value="1" />
		<input name="down" type="key" id="1073741905" value="1" />
		<input name="left" type="key" id="1073741904" value="1" />
		<input name="right" type="key" id="1073741903" value="1" />
		<input name="a" type="key" id="27" value="1" />
		<input name="b" type="key" id="13" value="1" />
		<input name="pagedown" type="key" id="34" value="1" />
		<input name="pageup" type="key" id="33" value="1" />
		<input name="select" type="key" id="8" value="1" />
		<input name="start" type="key" id="32" value="1" />
		<input name="x" type="key" id="61" value="1" />
		<input name="y" type="key" id="45" value="1" />
	</inputConfig>
</inputList>""")

    return Controller(
        name='Keyboard',
        type='keyboard',
        guid='-1',
        player_number=-1,
        index=-1,
        real_name='',
        device_path='',
        button_count=0,
        axis_count=0,
        hat_count=0,
        inputs_=Input.from_parent_element(cast(ET.Element, root.find('./inputConfig'))),
    )


def make_player_controller(controller: Controller, player_number: int, /) -> Controller:
    return controller.replace(
        player_number=player_number,
        index=player_number - 1,
        real_name=f'real name {player_number}',
        device_path=f'/dev/input/event{player_number}',
    )


@pytest.fixture
def generic_xbox_pad_p1(generic_xbox_pad: Controller) -> Controller:
    return make_player_controller(generic_xbox_pad, 1)


@pytest.fixture
def generic_xbox_pad_p2(generic_xbox_pad: Controller) -> Controller:
    return make_player_controller(generic_xbox_pad, 2)


@pytest.fixture
def gpio_controller_1_p1(gpio_controller_1: Controller) -> Controller:
    return make_player_controller(gpio_controller_1, 1)


@pytest.fixture
def gpio_controller_1_p2(gpio_controller_1: Controller) -> Controller:
    return make_player_controller(gpio_controller_1, 2)


@pytest.fixture
def ps3_controller_p1(ps3_controller: Controller) -> Controller:
    return make_player_controller(ps3_controller, 1)


@pytest.fixture
def ps3_controller_p2(ps3_controller: Controller) -> Controller:
    return make_player_controller(ps3_controller, 2)


@pytest.fixture
def one_player_controllers(generic_xbox_pad_p1: Controller) -> ControllerMapping:
    return {generic_xbox_pad_p1.player_number: generic_xbox_pad_p1}


@pytest.fixture
def two_player_controllers(generic_xbox_pad_p1: Controller, generic_xbox_pad_p2: Controller) -> ControllerMapping:
    return {
        generic_xbox_pad_p1.player_number: generic_xbox_pad_p1,
        generic_xbox_pad_p2.player_number: generic_xbox_pad_p2,
    }


@pytest.fixture
def video_mode(mocker: MockerFixture) -> Mock:
    video_mode = mocker.Mock()
    video_mode.getRefreshRate.return_value = '60.0'
    mocker.patch.dict('sys.modules', {'configgen.utils.videoMode': video_mode})
    return video_mode


@pytest.fixture
def vulkan_is_available(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.vulkan.is_available', return_value=False)


@pytest.fixture
def vulkan_has_discrete_gpu(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.vulkan.has_discrete_gpu', return_value=False)


@pytest.fixture
def vulkan_get_discrete_gpu_uuid(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_discrete_gpu_uuid', return_value=None)


@pytest.fixture
def vulkan_get_discrete_gpu_index(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_discrete_gpu_index', return_value=None)


@pytest.fixture
def wine_install_wine_trick(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.wine.install_wine_trick', return_value=None)


@pytest.fixture
def wine_regedit(mocker: MockerFixture) -> Any:
    return mocker.patch('configgen.utils.wine.regedit', return_value=None)


@dataclass(slots=True)
class MockEmulator:
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    renderconfig: dict[str, Any] = field(default_factory=dict)

    def isOptSet(self, key):
        if key in self.config:
            return True
        else:
            return False

    def getOptBoolean(self, key):
        true_values = {'1', 'true', 'on', 'enabled', True}
        value = self.config.get(key)

        if isinstance(value, str):
            value = value.lower()

        return value in true_values

    def getOptString(self, key):
        if key in self.config:
            if self.config[key]:
                return self.config[key]
        return ''


@pytest.fixture
def core() -> None:
    return


@pytest.fixture
def mock_system_base_config(core: str | None, emulator: str, request: pytest.FixtureRequest) -> dict[str, Any]:
    marker = cast('pytest.Mark | None', request.node.get_closest_marker('core'))

    if marker is not None:
        core = marker.args[0]

    return {'core': core or emulator, 'emulator': emulator, 'showFPS': 'false', 'uimode': 'Full'}


@pytest.fixture
def mock_system_config() -> None:
    return


@pytest.fixture
def mock_system(
    system_name: str,
    mock_system_base_config: Mapping[str, Any],
    mock_system_config: Mapping[str, Any] | None,
    request: pytest.FixtureRequest,
) -> MockEmulator:
    config = dict(mock_system_base_config)

    mock_system_config_marker = cast('pytest.Mark | None', request.node.get_closest_marker('mock_system_config'))
    system_name_marker = cast('pytest.Mark | None', request.node.get_closest_marker('system_name'))

    if mock_system_config_marker is not None:
        mock_system_config = mock_system_config_marker.args[0]

    if system_name_marker is not None:
        system_name = system_name_marker.args[0]

    if mock_system_config:
        config.update(mock_system_config)

    return MockEmulator(system_name, config=config)
