from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Literal

import pytest

from configgen.batoceraPaths import ROMS
from configgen.controller import Controller
from configgen.gun import Gun
from configgen.input import Input
from configgen.utils.evmapy import evmapy
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('subprocess_call')
class TestEvmapy:
    @pytest.fixture
    def player_one_input_device(self, mocker: MockerFixture) -> Mock:
        mock = mocker.Mock()
        mock.capabilities.return_value = {}
        return mock

    @pytest.fixture(autouse=True)
    def evdev_input_device(self, mocker: MockerFixture, player_one_input_device: Mock, evdev: Mock) -> Mock:
        evdev.ecodes.BTN_1 = 0x101
        evdev.ecodes.BTN_LEFT = 0x110
        evdev.ecodes.BTN_RIGHT = 0x111
        evdev.ecodes.BTN_MIDDLE = 0x112

        def input_device_side_effect(path: str) -> Mock:
            if path == '/dev/input/event1':
                return player_one_input_device

            return mocker.Mock()

        mock = mocker.Mock(side_effect=input_device_side_effect)
        evdev.InputDevice = mock

        return mock

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir('/var/run/evmapy')

        return fs

    @pytest.fixture
    def minimal_controller(self) -> Controller:
        return Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_={
                'start': Input(name='start', type='button', id='9', value='1', code='315'),
            },
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=1,
            axis_count=0,
            hat_count=0,
        )

    @pytest.fixture
    def hotkey_controller(self) -> Controller:
        return Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_={
                'foo': Input(name='foo', type='button', id='9', value='1'),
                'start': Input(name='start', type='button', id='9', value='1', code='315'),
                'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
            },
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=3,
            axis_count=0,
            hat_count=0,
        )

    @pytest.fixture
    def hotkey_duplicate_controller(self) -> Controller:
        return Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_={
                'select': Input(name='select', type='button', id='8', value='1', code='314'),
                'start': Input(name='start', type='button', id='9', value='1', code='315'),
                'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
            },
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=3,
            axis_count=0,
            hat_count=0,
        )

    @pytest.mark.parametrize(
        'keysfile',
        [
            '/usr/share/evmapy/any.keys',
            '/usr/share/evmapy/emulator.keys',
            '/usr/share/evmapy/system.keys',
            '/usr/share/evmapy/system.emulator.keys',
            '/userdata/system/configs/evmapy/any.keys',
            '/userdata/system/configs/evmapy/emulator.keys',
            '/userdata/system/configs/evmapy/system.keys',
            '/userdata/roms/system/rom_name.game/padto.keys',
            '/userdata/roms/system/rom_name.game.keys',
            '/usr/share/evmapy/hotkeys.keys',
            '/userdata/system/configs/hotkeys.keys',
        ],
    )
    def test_context(
        self,
        fs: FakeFilesystem,
        keysfile: str,
        minimal_controller: Controller,
        subprocess_call: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            keysfile,
            contents="""{
  "actions_player1": [
    {
      "trigger": "start",
      "type": "exec",
      "target": "killall -9 something",
      "description": "A trigger"
    }
  ]
}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(minimal_controller),
            [],
        ):
            assert subprocess_call.call_args_list == snapshot(name='subprocess.call')
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

        assert not Path('/var/run/evmapy_merged.keys').exists()
        assert subprocess_call.call_args_list == snapshot(name='subprocess.call post context')

    def test_context_merge(
        self,
        fs: FakeFilesystem,
        minimal_controller: Controller,
        subprocess_call: Mock,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        trigger_map = {
            '/usr/share/evmapy/any.keys': 'up',
            '/usr/share/evmapy/emulator.keys': 'select',
            '/usr/share/evmapy/system.keys': 'a',
            '/usr/share/evmapy/system.emulator.keys': 'b',
            '/userdata/system/configs/evmapy/any.keys': 'x',
            '/userdata/system/configs/evmapy/emulator.keys': 'y',
            '/userdata/system/configs/evmapy/system.keys': 'l2',
            '/userdata/roms/system/rom_name.game/padto.keys': 'r2',
            '/userdata/roms/system/rom_name.game.keys': 'l1',
            '/usr/share/evmapy/hotkeys.keys': 'l2',
            '/userdata/system/configs/hotkeys.keys': 'left',
        }

        for keysfile, trigger in trigger_map.items():
            fs.create_file(
                keysfile,
                contents=f"""{{
    "actions_player1": [
        {{
            "trigger": "{trigger}",
            "type": "exec",
            "target": "killall -9 {keysfile}"
        }},
        {{
            "trigger": ["hotkey", "{trigger}"],
            "type": "exec",
            "target": "killall -9 {keysfile}"
        }},
        {{
            "trigger": "start",
            "type": "exec",
            "target": "killall -9 {keysfile}"
        }},
        {{
            "trigger": ["hotkey", "start"],
            "type": "exec",
            "target": "killall -9 {keysfile}"
        }}
    ]
}}""",
            )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(generic_xbox_pad),
            [],
        ):
            assert subprocess_call.call_args_list == snapshot(name='subprocess.call')
            assert Path('/var/run/evmapy_merged.keys').read_text() == snapshot(name='evmapy_merged.keys')
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

        assert subprocess_call.call_args_list == snapshot(name='subprocess.call post context')

    def test_context_no_keysfiles(
        self,
        minimal_controller: Controller,
        subprocess_call: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(minimal_controller),
            [],
        ):
            assert subprocess_call.call_args_list == snapshot(name='subprocess.call')
            assert not Path('/var/run/evmapy_merged.keys').exists()
            assert not Path('/var/run/evmapy/event1.json').exists()

        assert subprocess_call.call_args_list == snapshot(name='subprocess.call post context')

    def test_context_cleanup_on_raise(
        self,
        fs: FakeFilesystem,
        minimal_controller: Controller,
        subprocess_call: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents="""{
  "actions_player1": [
    {
      "trigger": "start",
      "type": "exec",
      "target": "killall -9 something"
    }
  ]
}""",
        )

        with (
            pytest.raises(Exception, match=r'^Test Exception$'),
            evmapy(
                'system',
                'emulator',
                'core',
                ROMS / 'system' / 'rom_name.game',
                make_player_controller_list(minimal_controller),
                [],
            ),
        ):
            raise Exception('Test Exception')

        assert subprocess_call.call_args_list == snapshot(name='subprocess.call post context')

    def test_two_controllers_one_action_definition(
        self,
        fs: FakeFilesystem,
        minimal_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents="""{
  "actions_player1": [
    {
      "trigger": "start",
      "type": "exec",
      "target": "killall -9 something",
      "description": "A trigger"
    }
  ]
}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(minimal_controller, minimal_controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')
            assert not Path('/var/run/evmapy/event2.json').exists()

    @pytest.mark.parametrize('use_hotkey_or_select', [0, 1, 2], ids=['no hotkey', 'hotkey', 'select'])
    def test_trigger_key_button(
        self,
        fs: FakeFilesystem,
        use_hotkey_or_select: Literal[0, 1, 2],
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            'foo': Input(name='start', type='button', id='7', value='1', code=None),
            'start': Input(name='start', type='button', id='9', value='1', code='315'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        if not use_hotkey_or_select:
            trigger = '"start"'
        elif use_hotkey_or_select == 1:
            trigger = '["hotkey", "start"]'
        else:
            inputs['select'] = Input(name='select', type='button', id='8', value='1', code='314')
            trigger = '["select", "start"]'

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )
        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": {trigger},
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"]
    }}
  ]
}}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('with_hotkey', [True, False], ids=['with hotkey', 'without hotkey'])
    @pytest.mark.parametrize('hat_button', ['up', 'down', 'left', 'right'])
    def test_trigger_key_hat(
        self,
        fs: FakeFilesystem,
        hat_button: str,
        with_hotkey: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            'down': Input(name='down', type='hat', id='0', value='4', code='16'),
            'left': Input(name='left', type='hat', id='0', value='8', code='16'),
            'right': Input(name='right', type='hat', id='0', value='2', code='16'),
            'up': Input(name='up', type='hat', id='0', value='1', code='16'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )

        trigger = f'["hotkey", "{hat_button}"]' if with_hotkey else f'"{hat_button}"'

        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": {trigger},
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"]
    }}
  ]
}}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('with_hotkey', [True, False], ids=['with hotkey', 'without hotkey'])
    @pytest.mark.parametrize(
        ('axis_name', 'trigger_name'),
        [
            ('joystick1up', 'joystick1up'),
            ('joystick1up', 'joystick1down'),
            ('joystick1left', 'joystick1left'),
            ('joystick1left', 'joystick1right'),
            ('joystick2up', 'joystick2up'),
            ('joystick2up', 'joystick2down'),
            ('joystick2left', 'joystick2left'),
            ('joystick2left', 'joystick2right'),
            ('l2', 'l2'),
            ('r2', 'r2'),
        ],
    )
    def test_trigger_key_axis(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        player_one_input_device: Mock,
        with_hotkey: bool,
        axis_name: str,
        trigger_name: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            axis_name: Input(name=axis_name, type='axis', id='1', value='-1', code='1'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )

        trigger = f'["hotkey", "{trigger_name}"]' if with_hotkey else f'"{trigger_name}"'

        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": {trigger},
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"]
    }}
  ]
}}""",
        )

        player_one_input_device.capabilities.return_value = {
            3: [
                (1, mocker.Mock(min=-32768, max=32768)),
            ],
        }

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('input_first', [True, False], ids=['input first', 'input last'])
    @pytest.mark.parametrize('with_hotkey', [True, False], ids=['with hotkey', 'without hotkey'])
    @pytest.mark.parametrize('flip_value', [True, False], ids=['value flipped', 'value normal'])
    @pytest.mark.parametrize('trigger_name', ['up', 'down', 'left', 'right'])
    def test_trigger_key_axis_directional(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        player_one_input_device: Mock,
        with_hotkey: bool,
        flip_value: bool,
        trigger_name: str,
        input_first: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        input_map = {
            'down': Input(name='down', type='axis', id='1', value='-1' if flip_value else '1', code='1'),
            'up': Input(name='up', type='axis', id='1', value='1' if flip_value else '-1', code='1'),
            'left': Input(name='left', type='axis', id='0', value='1' if flip_value else '-1', code='0'),
            'right': Input(name='right', type='axis', id='0', value='-1' if flip_value else '1', code='0'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        inputs: dict[str, Input] = {}

        if input_first:
            inputs[trigger_name] = input_map[trigger_name]

        inputs.update((key, value) for key, value in input_map.items() if key != trigger_name)

        if not input_first:
            inputs[trigger_name] = input_map[trigger_name]

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )

        trigger = f'["hotkey", "{trigger_name}"]' if with_hotkey else f'"{trigger_name}"'

        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": {trigger},
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"]
    }}
  ]
}}""",
        )

        player_one_input_device.capabilities.return_value = {
            3: [
                (0, mocker.Mock(min=-32768, max=32768)),
                (1, mocker.Mock(min=-12768, max=12768)),
            ],
        }

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('has_abs', [True, False], ids=['has abs', 'has no abs'])
    @pytest.mark.parametrize('with_hotkey', [True, False], ids=['with hotkey', 'without hotkey'])
    def test_trigger_key_axis_capability_not_found(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        player_one_input_device: Mock,
        with_hotkey: bool,
        has_abs: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            'joystick1up': Input(name='joystick1up', type='axis', id='1', value='-1', code='1'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )

        trigger = '["hotkey", "joystick1up"]' if with_hotkey else '"joystick1up"'

        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": {trigger},
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"]
    }}
  ]
}}""",
        )

        player_one_input_device.capabilities.return_value = (
            {
                3: [
                    (4, mocker.Mock(min=-32768, max=32768)),
                ],
            }
            if has_abs
            else {1: []}
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    def test_trigger_key_with_mode(
        self,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            'start': Input(name='start', type='button', id='9', value='1', code='315'),
            'hotkey': Input(name='hotkey', type='button', id='8', value='1', code='314'),
        }

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )
        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents="""{
  "actions_player1": [
    {
      "trigger": "start",
      "type": "key",
      "target": ["KEY_LEFTCTRL", "KEY_Q"],
      "mode": "sequence"
    }
  ]
}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('has_missing_inputs', [True, False], ids=['has missing inputs', 'has all inputs'])
    @pytest.mark.parametrize('trigger', ['joystick1', 'joystick2'])
    def test_trigger_mouse(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        trigger: str,
        has_missing_inputs: bool,
        player_one_input_device: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        inputs = {
            f'{trigger}left': Input(name=f'{trigger}left', type='axis', id='0', value='-1', code='0'),
        }

        if not has_missing_inputs:
            inputs[f'{trigger}up'] = Input(name=f'{trigger}up', type='axis', id='1', value='-1', code='1')

        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_=inputs,
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )
        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_player1": [
    {{
      "trigger": "{trigger}",
      "type": "mouse"
    }}
  ]
}}""",
        )

        player_one_input_device.capabilities.return_value = {
            3: [
                (0, mocker.Mock(min=-32768, max=32768)),
                (1, mocker.Mock(min=-12768, max=12768)),
            ],
        }

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')

    @pytest.mark.parametrize('trigger', ['left', '2', ['left', 'right', 'middle'], ['middle', '2']], ids=str)
    def test_trigger_gun(
        self,
        fs: FakeFilesystem,
        trigger: str | list[str],
        snapshot: SnapshotAssertion,
    ) -> None:
        controller = Controller(
            name='Test Controller',
            type='joystick',
            guid='0000',
            inputs_={},
            device_path='',
            player_number=1,
            index=-1,
            real_name='Test Controller',
            button_count=0,
            axis_count=0,
            hat_count=0,
        )

        fs.create_file(
            '/usr/share/evmapy/any.keys',
            contents=f"""{{
  "actions_gun1": [
    {{
      "trigger": {json.dumps(trigger)},
      "type": "key",
      "target": [ "KEY_LEFTALT", "KEY_F4" ],
      "description": "Exit emulator"
    }},
    {{
      "trigger": "right",
      "type": "key",
      "target": "KEY_F4"
    }}
  ]
}}""",
        )

        with evmapy(
            'system',
            'emulator',
            'core',
            ROMS / 'system' / 'rom_name.game',
            make_player_controller_list(controller),
            [
                Gun(
                    node='/dev/input/event1',
                    mouse_index=0,
                    needs_cross=False,
                    needs_borders=False,
                    name='A gun',
                    buttons=['left', 'middle', 'right', '1'],
                ),
                Gun(
                    node='/dev/input/event2',
                    mouse_index=1,
                    needs_cross=False,
                    needs_borders=False,
                    name='Another gun',
                    buttons=[],
                ),
            ],
        ):
            assert Path('/var/run/evmapy/event1.json').read_text() == snapshot(name='event1.json')
