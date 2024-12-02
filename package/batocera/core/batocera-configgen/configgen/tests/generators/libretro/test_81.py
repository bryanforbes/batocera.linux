from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('81')
class TestLibretroGenerator81(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'81_chroma_81': ['automatic', 'disabled']},
            {'81_highres': ['automatic', 'none']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
