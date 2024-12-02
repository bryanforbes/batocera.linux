from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('fceumm')
@pytest.mark.fallback_system_name('nes')
class TestLibretroGeneratorFceumm(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'fceumm_show_crosshair': 'enabled'},
            {'fceumm_nospritelimit': ['enabled', 'disabled']},
            {'fceumm_cropoverscan': ['none', 'h', 'v', 'both']},
            {'fceumm_palette': 'asqrealc'},
            {'fceumm_ntsc_filter': 'composite'},
            {'fceumm_sndquality': 'High'},
            {'fceumm_overclocking': '2x-Postrender'},
            {'controller1_nes': '513'},
            {'controller2_nes': '258'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'fceumm_show_crosshair': ['disabled', 'enabled']}])
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
