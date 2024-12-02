from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('tyrquake')
@pytest.mark.fallback_system_name('quake')
class TestLibretroGeneratorTyrQuake(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'tyrquake_resolution': '960x720'},
            {'tyrquake_framerate': ['automatic', '10fps']},
            {'tyrquake_rumble': 'enabled'},
            {'tyrquake_controller1': ['1', '513', '773', '3']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize(
        'rom_name',
        [
            'Quake',
            'Quake Mission Pack 1 - Scourge of Armagon',
            'Quake Mission Pack 2 - Dissolution of Eternity',
        ],
    )
    def test_generate_quake_file(
        self,
        generator: Generator,
        rom_name: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'quake' / f'{rom_name}.quake',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
