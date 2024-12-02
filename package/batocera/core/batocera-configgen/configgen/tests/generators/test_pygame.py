from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.pygame.pygameGenerator import PygameGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestPygameGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[PygameGenerator]:
        return PygameGenerator

    def test_get_in_game_ratio(self, generator: PygameGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_execution_directory(self, generator: PygameGenerator) -> None:  # pyright: ignore
        assert generator.executionDirectory(SystemConfig({}), ROMS / 'pygame' / 'foo' / 'bar' / 'rom.pygame') == (
            ROMS / 'pygame' / 'foo' / 'bar'
        )

    def test_generate(
        self,
        generator: PygameGenerator,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'pygame' / 'rom.pygame',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
