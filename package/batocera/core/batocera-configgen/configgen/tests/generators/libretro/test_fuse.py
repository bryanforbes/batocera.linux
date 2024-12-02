from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('fuse')
class TestLibretroGeneratorFuse(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'fuse_machine': 'Spectrum 48K'},
            {'fuse_hide_border': 'enabled'},
            {'controller1_zxspec': '0'},
            {'controller2_zxspec': '1'},
            {'controller3_zxspec': '0'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
