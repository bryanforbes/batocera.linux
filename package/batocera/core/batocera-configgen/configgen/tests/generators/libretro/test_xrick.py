from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('xrick')
class TestLibretroGeneratorXRick(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'xrick_crop_borders': ['0', '1']},
            {'xrick_cheat1': ['0', '1']},
            {'xrick_cheat2': ['0', '1']},
            {'xrick_cheat3': ['0', '1']},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
