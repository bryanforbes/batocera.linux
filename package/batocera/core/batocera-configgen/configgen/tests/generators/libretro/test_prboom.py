from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('prboom')
class TestLibretroGeneratorPrBoom(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'prboom-resolution': '640x400'},
            {'prboom_controller1': ['1', '773', '3']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
