from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('swanstation')
class TestLibretroGeneratorSwanstation(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'swanstation_PatchFastBoot': 'true'},
            {'gpu_software': ['true', 'false']},
            {'gfxbackend': ['vulkan', 'gl', 'glcore', 'foo']},
            {'swanstation_resolution_scale': '2'},
            {'swanstation_pgxp': 'false'},
            {'swanstation_antialiasing': '4'},
            {'swanstation_texture_filtering': 'Bilinear'},
            {'swanstation_widescreen_hack': 'true', 'ratio': '16/9', 'bezel': 'none'},
            {'swanstation_CropMode': 'None'},
            {'swanstation_Controller1': ['1', '261', '517']},
            {'swanstation_Controller2': ['1', '261', '517']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'swanstation_Controller_ShowCrosshair': ['false', 'true']}])
    @pytest.mark.usefixtures('guns_need_crosses')
    def test_generate_crosses_config(
        self, generator: Generator, default_extension: str, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_core_config_matches(snapshot)
