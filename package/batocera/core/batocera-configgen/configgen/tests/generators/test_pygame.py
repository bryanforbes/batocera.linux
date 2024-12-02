from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

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
        assert generator.getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_execution_directory(self, generator: PygameGenerator) -> None:  # pyright: ignore
        assert (
            generator.executionDirectory({}, '/userdata/roms/pygame/foo/bar/rom.pygame')
            == '/userdata/roms/pygame/foo/bar'
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
                '/userdata/roms/pygame/rom.pygame',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
