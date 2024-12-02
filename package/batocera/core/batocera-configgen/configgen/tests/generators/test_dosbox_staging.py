from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.dosboxstaging.dosboxstagingGenerator import DosBoxStagingGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestDosBoxStagingGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DosBoxStagingGenerator]:
        return DosBoxStagingGenerator

    def test_generate(
        self, generator: DosBoxStagingGenerator, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_bat(
        self, generator: DosBoxStagingGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.bat')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_cfg(
        self, generator: DosBoxStagingGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.cfg')
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.conf')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_conf(
        self, generator: DosBoxStagingGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.conf')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
