from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.pyxel.pyxelGenerator import PyxelGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


class TestPyxelGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[PyxelGenerator]:
        return PyxelGenerator

    @pytest.mark.parametrize('extension', ['pyxapp', 'py'])
    def test_generate(
        self,
        generator: PyxelGenerator,
        extension: str,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'pyxel' / f'rom.{extension}',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
