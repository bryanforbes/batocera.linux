from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('bluemsx')
@pytest.mark.fallback_system_name('colecovision')
class TestLibretroGeneratorBluemsx(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [{'bluemsx_nospritelimits': ['True', 'False']}, {'bluemsx_overscan': 'enabled'}]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
