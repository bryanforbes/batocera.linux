from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('puae2021')
@pytest.mark.fallback_system_name('amiga500')
class TestLibretroGeneratorPuae2021(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'cpu_compatibility': ['compatible', 'exact']},
            {'cpu_compatibility': 'exact', 'cpu_multiplier': '1'},
            {'cpu_throttle': '-900.0'},
            {'video_standard': 'PAL'},
            {'video_resolution': 'superhires'},
            {'zoom_mode': ['automatic', 'minimum']},
            {'gfx_framerate': '1'},
            {'mouse_speed': '170'},
        ],
        {
            'amiga500': [
                {'puae_model': ['automatic', 'A500PLUS']},
                {'pad_options': 'disabled'},
                {'puae_floppy_speed': '0'},
                {'keyrah_mapping': 'disabled'},
                {'whdload': 'disabled'},
                {'disable_joystick': 'enabled'},
                {'controller1_puae': '517'},
                {'controller2_puae': '517'},
            ],
            'amiga1200': [
                {'puae_model': ['automatic', 'A4040']},
                {'pad_options': 'disabled'},
                {'puae_floppy_speed': '0'},
                {'keyrah_mapping': 'disabled'},
                {'whdload': 'disabled'},
                {'disable_joystick': 'enabled'},
            ],
            'amigacd32': [
                {'puae_model': ['automatic', 'CD32']},
                {'pad_options': 'disabled'},
                {'puae_cd_startup_delayed_insert': 'enabled'},
                {'puae_cd_speed': '0'},
                {'puae_cd32pad_options': 'jump'},
            ],
            'amigacdtv': [
                {'puae_model': ['automatic', 'CD32']},
                {'pad_options': 'jump'},
                {'puae_cd_startup_delayed_insert': 'enabled'},
                {'puae_cd_speed': '0'},
            ],
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
