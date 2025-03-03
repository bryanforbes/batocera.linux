from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.samcoupe.samcoupeGenerator import SamcoupeGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


class TestSamcoupeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SamcoupeGenerator]:
        return SamcoupeGenerator

    def test_generate(
        self,
        generator: SamcoupeGenerator,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'samcoupe' / 'rom.dsk',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
