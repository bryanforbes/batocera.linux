from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mgba')
@pytest.mark.fallback_system_name('gb')
class TestLibretroGeneratorMgba(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'skip_bios_mgba': ['True', 'False']},
            {'rumble_gain': ['1', '20']},
        ],
        {
            'gb': [
                {'sgb_borders': ['True', 'False']},
                {'color_correction': ['False', 'GBA']},
            ],
            'gbc': [
                {'sgb_borders': ['True', 'False']},
                {'color_correction': ['False', 'GBA']},
            ],
            'gba': [
                {'solar_sensor_level': '1'},
                {'frameskip_mgba': '1'},
            ],
            'sgb': [
                {'sgb_borders': ['True', 'False']},
            ],
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
