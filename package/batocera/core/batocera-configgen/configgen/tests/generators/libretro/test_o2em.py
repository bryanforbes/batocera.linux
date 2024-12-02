from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('o2em')
@pytest.mark.fallback_system_name('o2em')
class TestLibretroGeneratorO2EM(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'o2em_bios': 'jopac.bin'},
            {'o2em_region': ['autodetect', 'NTSC']},
            {'o2em_swap_gamepads': 'enabled'},
            {'o2em_crop_overscan': 'disabled'},
            {'o2em_mix_frames': 'mix'},
            {'o2em_low_pass_range': ['0', '10']},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
