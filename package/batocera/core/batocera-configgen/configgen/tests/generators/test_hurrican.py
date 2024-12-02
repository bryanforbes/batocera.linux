from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.hurrican.hurricanGenerator import HurricanGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestHurricanGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[HurricanGenerator]:
        return HurricanGenerator

    def test_generate(
        self,
        generator: HurricanGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'hurrican' / 'data' / 'levels')

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
        generator: HurricanGenerator,
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
                'configgen.generators.hurrican.hurricanGenerator',
                logging.ERROR,
                'ERROR: Game assets not installed. You can get them from the Batocera Content Downloader.',
            )
        ]
