from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.dosboxx.dosboxxGenerator import DosBoxxGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestDosBoxxGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DosBoxxGenerator]:
        return DosBoxxGenerator

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS / 'dosbox')

        return fs

    def test_generate(self, generator: DosBoxxGenerator, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
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
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')

    def test_generate_existing(
        self, generator: DosBoxxGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosboxx.conf',
            contents="""[something]
foo = true

[sdl]
bar = false
""",
        )

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
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')

    def test_generate_game_config(
        self, generator: DosBoxxGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosboxx.conf',
            contents="""[something]
foo = true
""",
        )
        fs.create_file(
            '/userdata/roms/dos/rom.pc/dosbox.cfg',
            contents="""[something]
foo = false
""",
        )

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
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')
