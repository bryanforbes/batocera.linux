from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.tsugaru.tsugaruGenerator import TsugaruGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


class TestTsugaruGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TsugaruGenerator]:
        return TsugaruGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'fmtowns'

    @pytest.fixture
    def emulator(self) -> str:
        return 'tsugaru'

    def test_generate(
        self,
        generator: TsugaruGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'fmtowns' / 'rom.bin',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['d88', 'iso', 'cue'])
    def test_generate_extension(
        self,
        generator: TsugaruGenerator,
        extension: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'fmtowns' / f'rom.{extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cdrom_speed': '2'},
            {'386dx': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: TsugaruGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'fmtowns' / 'rom.bin',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
