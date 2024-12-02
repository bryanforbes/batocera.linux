from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.tyrian.tyrianGenerator import TyrianGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestTyrianGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TyrianGenerator]:
        return TyrianGenerator

    def test_get_in_game_ratio(self, generator: TyrianGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: TyrianGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'tyrian' / 'data')

        assert (
            generator.generate(
                mocker.Mock(),
                mocker.Mock(),
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_not_downloaded(
        self,
        generator: TyrianGenerator,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        generator.generate(
            mocker.Mock(),
            mocker.Mock(),
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert caplog.record_tuples == [
            (
                'configgen.generators.tyrian.tyrianGenerator',
                logging.ERROR,
                'ERROR: Game assets not installed. You can get them from the Batocera Content Downloader.',
            )
        ]
