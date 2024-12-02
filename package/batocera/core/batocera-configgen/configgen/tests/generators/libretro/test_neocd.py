from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('neocd')
class TestLibretroGeneratorNeoCD(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'neocd_region': 'USA'},
            {'neocd_bios': 'neocd.bin (CDZ)'},
            {'neocd_per_content_saves': ['False', 'True']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
