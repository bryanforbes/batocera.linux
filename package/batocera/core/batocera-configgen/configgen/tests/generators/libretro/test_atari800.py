from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('atari800')
@pytest.mark.fallback_system_name('atari800')
class TestLibretroGeneratorAtari800(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        system_configs={
            'atari800': [
                {'atari800_system': '130XE (128K)'},
                {'atari800_ntscpal': 'PAL'},
                {'atari800_sioaccel': 'disabled'},
                {'atari800_artifacting': 'enabled'},
                {'atari800_resolution': '400x300'},
                {'atari800_internalbasic': 'enabled'},
            ],
            'atari5200': [
                {'atari800_opt2': 'enabled'},
            ],
        }
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
