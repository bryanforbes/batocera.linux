from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('kronos')
class TestLibretroGeneratorKronos(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'kronos_resolution': '480p'},
            {'kronos_meshmode': 'enabled'},
            {'kronos_bandingmode': 'enabled'},
            {'kronos_multitap': ['disabled', 'port1', 'port2', 'port12']},
            {'kronos_language_id': 'German'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
