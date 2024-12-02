from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('dice')
class TestLibretroGeneratorDice(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'ttl_use_mouse_pointer_for_paddle_1': 'disabled'},
            {'ttl_use_mouse_pointer_for_paddle_1': 'enabled'},
            {'ttl_retromouse_paddle0': 'disabled'},
            {'ttl_retromouse_paddle0': 'enabled'},
            {'ttl_retromouse_paddle1': 'disabled'},
            {'ttl_retromouse_paddle1': 'enabled'},
            {'ttl_retromouse_paddle2': 'disabled'},
            {'ttl_retromouse_paddle2': 'enabled'},
            {'ttl_retromouse_paddle3': 'disabled'},
            {'ttl_retromouse_paddle3': 'enabled'},
            {'ttl_retromouse_paddle0_x': 'x'},
            {'ttl_retromouse_paddle0_x': 'y'},
            {'ttl_retromouse_paddle0_y': 'x'},
            {'ttl_retromouse_paddle0_y': 'y'},
            {'ttl_retromouse_paddle1_x': 'x'},
            {'ttl_retromouse_paddle1_x': 'y'},
            {'ttl_retromouse_paddle1_y': 'x'},
            {'ttl_retromouse_paddle1_y': 'y'},
            {'ttl_retromouse_paddle2_x': 'x'},
            {'ttl_retromouse_paddle2_x': 'y'},
            {'ttl_retromouse_paddle2_y': 'x'},
            {'ttl_retromouse_paddle2_y': 'y'},
            {'ttl_retromouse_paddle3_x': 'x'},
            {'ttl_retromouse_paddle3_x': 'y'},
            {'ttl_retromouse_paddle3_y': 'x'},
            {'ttl_retromouse_paddle3_y': 'y'},
            {'ttl_paddle_keyboard_sensitivity': '125'},
            {'ttl_paddle_keyboard_sensitivity': '250'},
            {'ttl_paddle_joystick_sensitivity': '125'},
            {'ttl_paddle_joystick_sensitivity': '500'},
            {'ttl_retromouse_paddle_sensitivity': '125'},
            {'ttl_retromouse_paddle_sensitivity': '25'},
            {'ttl_wheel_keyjoy_sensitivity': '125'},
            {'ttl_wheel_keyjoy_sensitivity': '500'},
            {'ttl_throttle_keyjoy_sensitivity': '125'},
            {'ttl_throttle_keyjoy_sensitivity': '500'},
            {'ttl_dipswitch_1': '-1'},
            {'ttl_dipswitch_1': '0'},
            {'ttl_dipswitch_1': '1'},
            {'ttl_dipswitch_2': '-1'},
            {'ttl_dipswitch_2': '0'},
            {'ttl_dipswitch_2': '1'},
            {'ttl_dipswitch_3': '-1'},
            {'ttl_dipswitch_3': '0'},
            {'ttl_dipswitch_3': '1'},
            {'ttl_dipswitch16_1': '-1'},
            {'ttl_dipswitch16_1': '0'},
            {'ttl_dipswitch16_1': '1'},
            {'ttl_dipswitch16_2': '-1'},
            {'ttl_dipswitch16_2': '0'},
            {'ttl_dipswitch16_2': '1'},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
