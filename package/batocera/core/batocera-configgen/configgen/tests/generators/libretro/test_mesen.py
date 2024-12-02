from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mesen')
@pytest.mark.fallback_system_name('nes')
class TestLibretroGeneratorMesen(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'mesen_region': 'NTSC'},
            {'mesen_screenrotation': '90 degrees'},
            {'mesen_ntsc_filter': 'Composite (Blargg)'},
            {'mesen_nospritelimit': 'True'},
            {'mesen_palette': 'Nes Classic'},
            {'mesen_hdpacks': 'False'},
            {'mesen_fdsautoinsertdisk': 'True'},
            {'mesen_fdsfastforwardload': 'True'},
            {'mesen_ramstate': 'All 1s'},
            {'mesen_overclock': 'Low'},
            {'mesen_overclock_type': 'After NMI'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
