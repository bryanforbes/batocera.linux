from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS, SAVES
from configgen.generators.thextech.thextechGenerator import TheXTechGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestTheXTechGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TheXTechGenerator]:
        return TheXTechGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'thextech'

    @pytest.fixture
    def emulator(self) -> str:
        return 'thextech'

    def test_generate(
        self,
        generator: TheXTechGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'thextech' / 'rom.smbx',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'thextech').is_dir()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'rendering_mode': 'sw'},
            {'frameskip': '0'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: TheXTechGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'thextech' / 'rom.smbx',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'thextech').is_dir()
