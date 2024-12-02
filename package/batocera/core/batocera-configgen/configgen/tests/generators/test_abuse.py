from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.abuse.abuseGenerator import AbuseGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestAbuseGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[AbuseGenerator]:
        return AbuseGenerator

    def test_generate(
        self,
        generator: AbuseGenerator,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                '/userdata/roms/abuse/abuse.game',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
