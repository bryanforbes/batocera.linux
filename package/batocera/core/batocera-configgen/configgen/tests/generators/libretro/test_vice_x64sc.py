from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('vice_x64sc')
class TestLibretroGeneratorViceX64SC(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'c64_model': 'C64 NTSC auto'},
            {'vice_aspect_ratio': 'ntsc'},
            {'vice_zoom_mode': ['automatic', 'auto_disable']},
            {'vice_external_palette': 'cjam'},
            {'vice_retropad_options': 'disabled'},
            {'vice_joyport': '1'},
            {'vice_joyport_type': '2'},
            {'vice_ram_expansion_unit': '128kB'},
            {'vice_keyboard_pass_through': 'enabled'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
