from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('dolphin')
@pytest.mark.fallback_system_name('gamecube')
class TestLibretroGeneratorDolphin(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'wii_language': 'French'},
            {'wii_resolution': 'x2 (1280 x 1056)'},
            {'wii_anisotropic': '2x'},
            {'wii_widescreen_hack': 'enabled'},
            {'wii_shader_mode': 'sync UberShaders'},
            {'wii_osd': 'disabled'},
        ],
        {
            'wii': [
                {'wii_widescreen': 'disabled'},
                {'controller1_wii': '513'},
                {'controller2_wii': '769'},
                {'controller3_wii': '1025'},
                {'controller4_wii': '1281'},
            ]
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
