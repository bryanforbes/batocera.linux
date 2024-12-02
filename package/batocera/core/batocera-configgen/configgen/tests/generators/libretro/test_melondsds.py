from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('melondsds')
class TestLibretroGeneratorMelonDSDS(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'melondsds_console_mode': 'DSi'},
            {'melondsds_render_mode': 'opengl'},
            {'melondsds_resolution': '2'},
            {'melondsds_poygon': 'enabled'},
            {'melondsds_filtering': 'linear'},
            {'melondsds_cursor': ['never', 'touching', 'timeout', 'always']},
            {'melondsds_cursor_timeout': '1'},
            {'melondsds_touchmode': ['joystick', 'pointer']},
            {'melondsds_dns': '95.217.77.181'},
            {'melondsds_language': 'en'},
            {'melondsds_colour': '0'},
            {'melondsds_month': '1'},
            {'melondsds_day': '1'},
            {'melondsds_show_unsupported': 'enabled'},
            {'melondsds_show_bios': 'enabled'},
            {'melondsds_show_layout': 'enabled'},
            {'melondsds_show_mic': 'enabled'},
            {'melondsds_show_camera': 'enabled'},
            {'melondsds_show_lid': 'enabled'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
