from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('pce_fast')
@pytest.mark.fallback_system_name('pcengine')
class TestLibretroGeneratorPceFast(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'pce_nospritelimit': 'disabled'}, {'controller1_pce': '2'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
