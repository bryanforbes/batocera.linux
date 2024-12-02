from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('cap32')
@pytest.mark.fallback_system_name('amstradcpc')
class TestLibretroGeneratorCap32(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'cap32_model': '464'},
            {'cap32_ram': '192'},
            {'cap32_colour': '16bit'},
            {'cap32_language': 'spanish'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
