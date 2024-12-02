from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.ikemen.ikemenGenerator import IkemenGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestIkemenGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[IkemenGenerator]:
        return IkemenGenerator

    def test_generate(
        self,
        generator: IkemenGenerator,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ikemen' / 'rom.ikemen',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: IkemenGenerator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json',
            contents="""{
  "KeyConfig": false,
  "JoystickConfig": true,
  "Fullscreen": false,
  "foo": "bar"
}""",
        )
        generator.generate(
            mocker.Mock(),
            ROMS / 'ikemen' / 'rom.ikemen',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json').read_text() == snapshot
