from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('pcsx2')
class TestLibretroGeneratorPCSX2(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'lr_pcsx2_fast_boot': 'enabled'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
