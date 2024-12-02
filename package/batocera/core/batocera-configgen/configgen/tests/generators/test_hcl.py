from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.hcl.hclGenerator import HclGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestHclGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[HclGenerator]:
        return HclGenerator

    def test_generate(
        self,
        generator: HclGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'hcl' / 'data' / 'map')

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
        generator: HclGenerator,
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
                'configgen.generators.hcl.hclGenerator',
                logging.ERROR,
                'ERROR: Game assets not installed. You can get them from the Batocera Content Downloader.',
            )
        ]
