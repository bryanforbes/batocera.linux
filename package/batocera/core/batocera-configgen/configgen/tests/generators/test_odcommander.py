from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.odcommander.odcommanderGenerator import OdcommanderGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


class TestOdcommanderGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OdcommanderGenerator]:
        return OdcommanderGenerator

    def test_generate(
        self,
        generator: OdcommanderGenerator,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                mocker.Mock(),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
