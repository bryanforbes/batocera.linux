from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('desmume')
class TestLibretroGeneratorDesmume(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'internal_resolution_desmume': '512x384'},
            {'texture_scaling': '2'},
            {'texture_smoothing': 'enabled'},
            {'multisampling': '2'},
            {'screens_layout': 'bottom/top'},
            {'frameskip_desmume': '1'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
