from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mrboom')
class TestLibretroGeneratorMrBoom(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'mrboom-aspect': 'Color'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
