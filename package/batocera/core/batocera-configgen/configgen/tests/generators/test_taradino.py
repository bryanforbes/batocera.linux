from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.taradino.taradinoGenerator import TaradinoGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


class TestTaradinoGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TaradinoGenerator]:
        return TaradinoGenerator

    def test_generate(
        self,
        generator: TaradinoGenerator,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'rott' / 'rom.rott',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
