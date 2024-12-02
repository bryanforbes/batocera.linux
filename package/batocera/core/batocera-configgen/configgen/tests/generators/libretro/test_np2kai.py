from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('np2kai')
class TestLibretroGeneratorNp2Kai(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'np2kai_model': 'PC-286'},
            {'np2kai_cpu_feature': 'Intel i486DX'},
            {'np2kai_clk_mult': '6'},
            {'np2kai_ExMemory': '13'},
            {'np2kai_gdc': 'uPD72020'},
            {'np2kai_skipline': ['Full 255 lines', 'True', 'False']},
            {'np2kai_realpal': ['True', 'False']},
            {'np2kai_SNDboard': 'None'},
            {'np2kai_jast_snd': ['True', 'False']},
            {'np2kai_joymode': 'Mouse'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)
