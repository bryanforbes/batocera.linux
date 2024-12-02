from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('melonds')
class TestLibretroGeneratorMelonDS(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'melonds_console_mode': 'DSi'},
            {'melonds_boot_directly': 'disabled'},
            {'melonds_use_fw_settings': 'enable'},
            {'melonds_language': 'French'},
            {
                'melonds_screen_layout': [
                    'Hybrid Top-Ratio2',
                    'Hybrid Top-Ratio3',
                    'Hybrid Bottom-Ratio2',
                    'Hybrid Bottom-Ratio3',
                    'Bottom/Top',
                ]
            },
            {'melonds_touch_mode': 'Mouse'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
