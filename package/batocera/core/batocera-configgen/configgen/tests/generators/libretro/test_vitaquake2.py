from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('vitaquake2')
class TestLibretroGeneratorVitaQuake2(LibretroBaseCoreTest):
    @pytest.mark.parametrize(
        'rom_name',
        [
            'Quake II',
            'Quake II - Ground Zero',
            'Quake II - The Reckoning',
            'Quake II - Zaero',
            'Quake II - Slight Mechanical Destruction',
        ],
    )
    def test_generate_game_filename(
        self,
        generator: Generator,
        rom_name: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                f'/userdata/roms/vitaquake2/{rom_name}.quake2',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
