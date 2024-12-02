from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('virtualjaguar')
@pytest.mark.fallback_system_name('jaguar')
class TestLibretroGeneratorVirtualJaguar(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'usefastblitter': 'disabled'},
            {'bios_vj': 'disabled'},
            {'doom_res_hack': 'enabled'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
