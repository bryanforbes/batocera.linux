from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('mame078plus')
@pytest.mark.fallback_system_name('mame')
class TestLibretroGeneratorMame078Plus(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'mame2003-plus_analog': ['analog', 'digital']},
            {'mame2003-plus_frameskip': '1'},
            {'mame2003-plus_input_interface': ['retropad', 'keyboard', 'simultaneous']},
            {'mame2003-plus_tate_mode': ['disabled', 'enabled']},
            {'mame2003-plus_neogeo_bios': 'us'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'mame2003-plus_crosshair_enabled': ['disabled', 'enabled']}])
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
