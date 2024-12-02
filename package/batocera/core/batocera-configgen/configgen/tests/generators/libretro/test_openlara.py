from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('openlara')
class TestLibretroGeneratorOpenLara(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'lara-resolution': '1600x1200'},
            {'lara-framerate': '30fps'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
