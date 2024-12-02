from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('yabasanshiro')
class TestLibretroGeneratorYabasanshiro(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'resolution_mode': '2x'},
            {'multitap_yabasanshiro': ['disabled', 'port1', 'port2', 'port12']},
            {'controller1_saturn': '5'},
            {'controller2_saturn': '5'},
            {'yabasanshiro_language': 'spanish'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
