from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('opera')
@pytest.mark.fallback_system_name('3do')
class TestLibretroGeneratorOpera(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'high_resolution': 'disabled'},
            {'cpu_overclock': '1.1x (13.75Mhz)'},
            {'active_devices': '2'},
            {'game_fixes_opera': ['disabled', 'timing_hack1', 'timing_hack3', 'timing_hack5', 'timing_hack6']},
            {'opera_nvram_storage': 'shared'},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    def test_generate_existing_3ds_cfg(
        self,
        generator: Generator,
        default_extension: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom_disc.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_core_config_matches(snapshot)
