from __future__ import annotations

from argparse import Namespace
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BATOCERA_ES_DIR, HOME, USER_ES_DIR
from configgen.controller import Controller, get_mapping_axis_relaxed_values
from configgen.input import Input

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock.plugin import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.fixture(autouse=True)
def evdev(evdev: Mock) -> Mock:
    evdev.ecodes.EV_ABS = 3
    evdev.ecodes.ABS_HAT0X = 0x10
    return evdev


class TestController:
    def test_init(self, snapshot: SnapshotAssertion) -> None:
        input = Input(name='a', type='button', id='1', value='1', code='305')
        inputs = {input.name: input}
        controller = Controller(
            name='name',
            type='joystick',
            guid='guid',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_=inputs,
        )
        assert controller == snapshot
        assert controller.inputs is not inputs

    def test_generate_sdl_game_db_line(self, snapshot: SnapshotAssertion) -> None:
        controller = Controller(
            name='Xbox 360 Wireless Receiver (XBOX)',
            type='joystick',
            guid='030000005e040000a102000007010000',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_={
                'a': Input(name='a', type='button', id='1', value='1', code='305'),
                'b': Input(name='b', type='button', id='0', value='1', code='304'),
                'down': Input(name='down', type='button', id='16', value='1', code='707'),
                'right': Input(name='right', type='axis', id='0', value='1', code='0'),
                'left': Input(name='left', type='axis', id='0', value='-1', code='0'),
                'up': Input(name='up', type='hat', id='0', value='1', code='16'),
                'hotkey': Input(name='hotkey', type='button', id='10', value='1', code='316'),
                'joystick1left': Input(name='joystick1left', type='axis', id='0', value='-1', code='0'),
                'joystick1up': Input(name='joystick1up', type='axis', id='1', value='-1', code='1'),
                'joystick2up': Input(name='joystick2up', type='axis', id='3', value='1', code='5'),
                'l2': Input(name='l2', type='axis', id='2', value='1', code='2'),
                'pagedown': Input(name='pagedown', type='key', id='45', value='1', code=None),
                'foo': Input(name='foo', type='key', id='45', value='1', code=None),
            },
        )

        assert controller.generate_sdl_game_db_line() == snapshot

    def test_generate_sdl_game_db_line_ignore_buttons(self, snapshot: SnapshotAssertion) -> None:
        controller = Controller(
            name='Xbox 360 Wireless Receiver (XBOX)',
            type='joystick',
            guid='030000005e040000a102000007010000',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_={
                'a': Input(name='a', type='button', id='1', value='1', code='305'),
                'b': Input(name='b', type='button', id='0', value='1', code='304'),
                'down': Input(name='down', type='button', id='16', value='1', code='707'),
                'right': Input(name='right', type='axis', id='0', value='1', code='0'),
                'left': Input(name='left', type='axis', id='0', value='-1', code='0'),
                'up': Input(name='up', type='hat', id='0', value='1', code='16'),
                'hotkey': Input(name='hotkey', type='button', id='10', value='1', code='316'),
                'joystick1left': Input(name='joystick1left', type='axis', id='0', value='-1', code='0'),
                'joystick1up': Input(name='joystick1up', type='axis', id='1', value='-1', code='1'),
                'joystick2up': Input(name='joystick2up', type='axis', id='3', value='1', code='5'),
                'l2': Input(name='l2', type='axis', id='2', value='1', code='2'),
                'pagedown': Input(name='pagedown', type='key', id='45', value='1', code=None),
                'foo': Input(name='foo', type='key', id='45', value='1', code=None),
            },
        )

        assert controller.generate_sdl_game_db_line(ignore_buttons=['hotkey']) == snapshot

    def test_generate_sdl_game_db_line_no_hotkey(self, snapshot: SnapshotAssertion) -> None:
        controller = Controller(
            name='Xbox 360 Wireless Receiver (XBOX)',
            type='joystick',
            guid='030000005e040000a102000007010000',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_={
                'a': Input(name='a', type='button', id='1', value='1', code='305'),
                'b': Input(name='b', type='button', id='0', value='1', code='304'),
                'down': Input(name='down', type='button', id='16', value='1', code='707'),
                'right': Input(name='right', type='axis', id='0', value='1', code='0'),
                'left': Input(name='left', type='axis', id='0', value='-1', code='0'),
                'up': Input(name='up', type='hat', id='0', value='1', code='16'),
                'joystick1left': Input(name='joystick1left', type='axis', id='0', value='-1', code='0'),
                'joystick1up': Input(name='joystick1up', type='axis', id='1', value='-1', code='1'),
                'joystick2up': Input(name='joystick2up', type='axis', id='3', value='1', code='5'),
                'l2': Input(name='l2', type='axis', id='2', value='1', code='2'),
                'pagedown': Input(name='pagedown', type='key', id='45', value='1', code=None),
                'foo': Input(name='foo', type='key', id='45', value='1', code=None),
            },
        )

        assert controller.generate_sdl_game_db_line() == snapshot

    def test_generate_sdl_game_db_line_hotkey_not_button(self, snapshot: SnapshotAssertion) -> None:
        controller = Controller(
            name='Xbox 360 Wireless Receiver (XBOX)',
            type='joystick',
            guid='030000005e040000a102000007010000',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_={
                'a': Input(name='a', type='button', id='1', value='1', code='305'),
                'b': Input(name='b', type='button', id='0', value='1', code='304'),
                'down': Input(name='down', type='button', id='16', value='1', code='707'),
                'right': Input(name='right', type='axis', id='0', value='1', code='0'),
                'left': Input(name='left', type='axis', id='0', value='-1', code='0'),
                'up': Input(name='up', type='hat', id='0', value='1', code='16'),
                'hotkey': Input(name='hotkey', type='key', id='0', value='1', code='31546504'),
                'joystick1left': Input(name='joystick1left', type='axis', id='0', value='-1', code='0'),
                'joystick1up': Input(name='joystick1up', type='axis', id='1', value='-1', code='1'),
                'joystick2up': Input(name='joystick2up', type='axis', id='3', value='1', code='5'),
                'l2': Input(name='l2', type='axis', id='2', value='1', code='2'),
                'pagedown': Input(name='pagedown', type='key', id='45', value='1', code=None),
                'foo': Input(name='foo', type='key', id='45', value='1', code=None),
            },
        )

        assert controller.generate_sdl_game_db_line() == snapshot

    def test_generate_sdl_game_db_line_hotkey_raises(self) -> None:
        controller = Controller(
            name='Xbox 360 Wireless Receiver (XBOX)',
            type='joystick',
            guid='030000005e040000a102000007010000',
            player_number=1,
            index=0,
            real_name='real name',
            device_path='/dev/null',
            button_count=1,
            hat_count=2,
            axis_count=3,
            inputs_={
                'a': Input(name='a', type='foo', id='1', value='1', code='305'),
            },
        )

        with pytest.raises(ValueError, match="^unknown key type: 'foo'"):
            controller.generate_sdl_game_db_line()

    def test_load_for_players(self, fs: FakeFilesystem, snapshot: SnapshotAssertion) -> None:
        fs.create_file(
            BATOCERA_ES_DIR / 'es_input.cfg',
            contents="""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="Test Controller" deviceGUID="1">
		<input name="a" type="button" id="0" value="1" code="111" />
	</inputConfig>
	<inputConfig type="joystick" deviceName="Test Controller 2" deviceGUID="3">
		<input name="x" type="button" id="0" value="1" code="111" />
	</inputConfig>
</inputList>
""",
        )
        fs.create_file(
            USER_ES_DIR / 'es_input.cfg',
            contents="""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="Test Controller" deviceGUID="2">
		<input name="b" type="button" id="0" value="1" code="222" />
	</inputConfig>
</inputList>
""",
        )

        assert (
            Controller.load_for_players(
                7,
                Namespace(
                    # P1: matches user test controller with guid and name
                    p1index=0,
                    p1guid='2',
                    p1name='Test Controller',
                    p1devicepath='/dev/event/input1',
                    p1nbbuttons=1,
                    p1nbhats=2,
                    p1nbaxes=3,
                    # P2: matches user test controller with guid
                    p2index=22,
                    p2guid='2',
                    p2name='Something else',
                    p2devicepath='/dev/event/input2',
                    p2nbbuttons=1,
                    p2nbhats=2,
                    p2nbaxes=3,
                    # P3: matches user test controller with name
                    p3index=2,
                    p3guid='20',
                    p3name='Test Controller',
                    p3devicepath='/dev/event/input3',
                    p3nbbuttons=1,
                    p3nbhats=2,
                    p3nbaxes=3,
                    # P4: matches system test controller with name and guid
                    p4index=4,
                    p4guid='1',
                    p4name='Test Controller',
                    p4devicepath='/dev/event/input4',
                    p4nbbuttons=1,
                    p4nbhats=2,
                    p4nbaxes=3,
                    # P5: matches no controllers
                    p5index=5,
                    p5guid='4',
                    p5name='Non existent',
                    p5devicepath='/dev/event/input5',
                    p5nbbuttons=1,
                    p5nbhats=2,
                    p5nbaxes=3,
                    # P6: matches system test controller 2 with name and guid
                    p6index=6,
                    p6guid='3',
                    p6name='Test controller 2',
                    p6devicepath='/dev/event/input6',
                    p6nbbuttons=1,
                    p6nbhats=2,
                    p6nbaxes=3,
                    # P7: not passed to emulatorlauncher
                    p7index=None,
                    p7guid=None,
                    p7name=None,
                    p7devicepath=None,
                    p7nbbuttons=None,
                    p7nbhats=None,
                    p7nbaxes=None,
                ),
            )
            == snapshot
        )

    @pytest.mark.usefixtures('fs')
    def test_load_for_players_no_files(self) -> None:
        assert (
            Controller.load_for_players(
                7,
                Namespace(
                    # P1: matches user test controller with guid and name
                    p1index=0,
                    p1guid='2',
                    p1name='Test Controller',
                    p1devicepath='/dev/event/input1',
                    p1nbbuttons=1,
                    p1nbhats=2,
                    p1nbaxes=3,
                    # P2: matches user test controller with guid
                    p2index=22,
                    p2guid='2',
                    p2name='Something else',
                    p2devicepath='/dev/event/input2',
                    p2nbbuttons=1,
                    p2nbhats=2,
                    p2nbaxes=3,
                    # P3: matches user test controller with name
                    p3index=2,
                    p3guid='20',
                    p3name='Test Controller',
                    p3devicepath='/dev/event/input3',
                    p3nbbuttons=1,
                    p3nbhats=2,
                    p3nbaxes=3,
                    # P4: matches system test controller with name and guid
                    p4index=4,
                    p4guid='1',
                    p4name='Test Controller',
                    p4devicepath='/dev/event/input4',
                    p4nbbuttons=1,
                    p4nbhats=2,
                    p4nbaxes=3,
                    # P5: matches no controllers
                    p5index=5,
                    p5guid='4',
                    p5name='Non existent',
                    p5devicepath='/dev/event/input5',
                    p5nbbuttons=1,
                    p5nbhats=2,
                    p5nbaxes=3,
                    # P6: matches system test controller 2 with name and guid
                    p6index=6,
                    p6guid='3',
                    p6name='Test controller 2',
                    p6devicepath='/dev/event/input6',
                    p6nbbuttons=1,
                    p6nbhats=2,
                    p6nbaxes=3,
                    # P7: not passed to emulatorlauncher
                    p7index=None,
                    p7guid=None,
                    p7name=None,
                    p7devicepath=None,
                    p7nbbuttons=None,
                    p7nbhats=None,
                    p7nbaxes=None,
                ),
            )
            == {}
        )


@pytest.mark.usefixtures('fs')
def test_get_mapping_axis_relaxed_values(generic_xbox_pad: Controller) -> None:
    assert get_mapping_axis_relaxed_values(generic_xbox_pad) == {}


def test_get_mapping_axis_relaxed_values_with_cache_file(
    mocker: MockerFixture, evdev: Mock, fs: FakeFilesystem, ps3_controller: Controller
) -> None:
    fs.create_file(
        HOME / '.sdl2' / f'{ps3_controller.guid}_{ps3_controller.name}.cache',
        contents="""6
4000
-4000
3999
4001
-4001
-3999
""",
    )

    mock_input_device = mocker.Mock()
    mock_input_device.capabilities.return_value = {
        0: [],
        1: [],
        3: [
            (0, {}),
            (1, {}),
            (2, {}),
            (3, {}),
            (4, {}),
            (5, {}),
            (0x10, {}),
        ],
    }

    evdev.InputDevice.return_value = mock_input_device

    assert get_mapping_axis_relaxed_values(ps3_controller) == {
        'joystick1left': {'centered': False, 'reversed': False},
        'joystick1up': {'centered': False, 'reversed': False},
        'joystick2left': {'centered': False, 'reversed': True},
        'joystick2up': {'centered': False, 'reversed': False},
        'l2': {'centered': True, 'reversed': False},
        'r2': {'centered': True, 'reversed': False},
    }


def test_get_mapping_axis_relaxed_values_with_cache_file_not_found(
    mocker: MockerFixture, evdev: Mock, fs: FakeFilesystem, ps3_controller: Controller
) -> None:
    fs.create_file(
        HOME / '.sdl2' / f'{ps3_controller.guid}_{ps3_controller.name}.cache',
        contents="""1
4001
""",
    )

    mock_input_device = mocker.Mock()
    mock_input_device.capabilities.return_value = {
        0: [],
        1: [],
        3: [
            (0x10, {}),
        ],
    }

    evdev.InputDevice.return_value = mock_input_device

    assert get_mapping_axis_relaxed_values(ps3_controller) == {
        'joystick1left': {'centered': True, 'reversed': False},
        'joystick1up': {'centered': True, 'reversed': False},
        'joystick2left': {'centered': True, 'reversed': False},
        'joystick2up': {'centered': True, 'reversed': False},
        'l2': {'centered': True, 'reversed': False},
        'r2': {'centered': True, 'reversed': False},
    }
