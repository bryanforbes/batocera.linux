from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('nestopia')
@pytest.mark.fallback_system_name('nes')
class TestLibretroGeneratorNestopia(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'nestopia_nospritelimit': ['enabled', 'disabled']},
            {'nestopia_cropoverscan': ['none', 'h', 'v', 'both']},
            {'nestopia_palette': 'cxa2025as'},
            {'nestopia_blargg_ntsc_filter': 'composite'},
            {'nestopia_overclock': '2x'},
            {'nestopia_select_adapter': ['automatic', 'ntsc']},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'nestopia_show_crosshair': ['disabled', 'enabled']}])
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
