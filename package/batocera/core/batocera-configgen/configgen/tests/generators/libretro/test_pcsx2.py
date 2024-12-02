from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('pcsx2')
class TestLibretroGeneratorPCSX2(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'lr_pcsx2_fast_boot': 'enabled'},
            {'lr_pcsx2_fast_cdvd': 'enabled'},
            {'lr_pcsx2_fast_cheats': 'enabled'},
            {'lr_pcsx2_language_unlock': 'enabled'},
            {'lr_pcsx2_resolution': '2x Native (~720p)'},
            {'lr_pcsx2_texture_filtering': 'Nearest'},
            {'lr_pcsx2_trilinear_filtering': 'Trilinear (PS2)'},
            {'lr_pcsx2_anisotropic': '2x'},
            {'lr_pcsx2_dithering': 'Scaled'},
            {'lr_pcsx2_blending': 'Medium'},
            {'ratio': ['16/9', 'full', '16/10', '21/9', '32/9']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
