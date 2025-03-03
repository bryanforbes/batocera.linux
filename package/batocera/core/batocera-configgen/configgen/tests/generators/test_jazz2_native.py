from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.config import SystemConfig
from configgen.generators.jazz2_native.jazz2_nativeGenerator import Jazz2_NativeGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestJazz2_NativeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Jazz2_NativeGenerator]:
        return Jazz2_NativeGenerator

    def test_get_in_game_ratio(self, generator: Jazz2_NativeGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Jazz2_NativeGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/usr/share/jazz2')

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

        assert Path('/usr/share/jazz2/gamecontrollerdb.txt').read_text() == snapshot(name='controllerdb')
