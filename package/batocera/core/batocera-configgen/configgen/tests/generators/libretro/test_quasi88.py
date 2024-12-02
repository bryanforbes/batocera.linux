from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('quasi88')
class TestLibretroGeneratorQuasi88(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [{'q88_basic_mode': 'N88 V1H'}, {'q88_cpu_clock': '2'}, {'q88_pcg-8100': 'enabled'}]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
