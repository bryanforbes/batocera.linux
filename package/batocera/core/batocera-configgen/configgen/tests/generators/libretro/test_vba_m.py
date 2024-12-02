from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('vba-m')
@pytest.mark.fallback_system_name('gba')
class TestLibretroGeneratorVbaM(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        system_configs={
            'gb': [
                {'palettes': 'original gameboy'},
                {'gbcoloroption_gb': 'enabled'},
                {'showborders_gb': 'enabled'},
            ],
            'gbc': [
                {'gbcoloroption_gbc': 'enabled'},
                {'showborders_gbc': 'enabled'},
            ],
            'gba': [
                {'solarsensor': '1'},
                {'gyro_sensitivity': '15'},
                {'tilt_sensitivity': '20'},
            ],
        }
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
