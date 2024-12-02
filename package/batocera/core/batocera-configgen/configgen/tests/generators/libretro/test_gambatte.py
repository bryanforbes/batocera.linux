from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('gambatte')
@pytest.mark.fallback_system_name('gb')
class TestLibretroGeneratorGambatte(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'gb_bootloader': 'disabled'},
            {'gb_mix_frames': 'mix'},
        ],
        {
            'gb': [
                {
                    'gb_colorization': [
                        'none',
                        'GB - Disabled',
                        'GB - SmartColor',
                        'GBC - Game Specific',
                        'custom',
                        'GB - DMG',
                    ]
                },
            ],
            'gbc': [
                {'gbc_color_correction': 'always'},
            ],
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
