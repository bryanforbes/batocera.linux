from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mednafen_psx')
class TestLibretroGeneratorMednafenPSX(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'beetle_psx_hw_skip_bios': 'enabled'},
            {'beetle_psx_hw_cpu_freq_scale': '50%'},
            {'beetle_psx_hw_internal_resolution': '2x'},
            {'beetle_psx_hw_widescreen_hack': 'enabled', 'ratio': '16/9', 'bezel': 'none'},
            {'beetle_psx_hw_frame_duping': 'enabled'},
            {'beetle_psx_hw_cpu_dynarec': 'execute'},
            {'beetle_psx_hw_dynarec_invalidate': 'dma'},
            {'multitap_mednafen': ['disabled', 'port1', 'port2', 'port12']},
            {'beetle_psx_hw_Controller1': ['1', '261']},
            {'beetle_psx_hw_Controller2': ['1', '261']},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
