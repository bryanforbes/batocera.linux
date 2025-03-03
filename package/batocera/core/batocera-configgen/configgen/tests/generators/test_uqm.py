from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS, SAVES
from configgen.generators.uqm.uqmGenerator import UqmGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


class TestUqmGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[UqmGenerator]:
        return UqmGenerator

    def test_generate(
        self,
        generator: UqmGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'uqm')

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

        assert (SAVES / 'uqm' / 'teams').exists()
        assert (SAVES / 'uqm' / 'save').exists()
        assert (ROMS / 'uqm' / 'version').read_text() == ''

    def test_generate_existing(
        self,
        generator: UqmGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'uqm' / 'version', contents='foo')

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

        assert (ROMS / 'uqm' / 'version').read_text() == 'foo'
