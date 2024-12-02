from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('pokemini')
class TestLibretroGeneratorPokemini(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'pokemini_lcdfilter': 'none'}, {'pokemini_lcdmode': '3shades'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
