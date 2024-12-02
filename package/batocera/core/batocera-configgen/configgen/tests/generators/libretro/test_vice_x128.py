from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('vice_x128')
class TestLibretroGeneratorViceX128(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'c128_model': 'C128 NTSC'},
            {'vice_aspect_ratio': 'ntsc'},
            {'vice_zoom_mode': ['automatic', 'auto_disable']},
            {'vice_external_palette': 'cjam'},
            {'vice_retropad_options': 'jump'},
            {'vice_joyport': '1'},
            {'vice_joyport_type': '2'},
            {'vice_keyboard_pass_through': 'enabled'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
