from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.dosbox.dosboxGenerator import DosBoxGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


class TestDosBoxGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DosBoxGenerator]:
        return DosBoxGenerator

    @pytest.fixture
    def emulator(self) -> str:
        return 'dosbox'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS / 'dosbox')

        return fs

    def test_generate(self, generator: DosBoxGenerator, mock_system: Emulator, snapshot: SnapshotAssertion) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path(CONFIGS / 'dosbox' / 'dosbox-custom.conf').read_text() == snapshot(name='config')

    def test_generate_existing(
        self, generator: DosBoxGenerator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosbox.conf',
            contents="""[foo]
bar = baz

[sdl]
output = 1
ham = spam

[cpu]
core = 2
cputype = 3
cycles = 4
blah = bam
""",
        )
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosbox-custom.conf',
            contents="""[foo]
bar = custom baz

[sdl]
output = 8
ham = custom spam

[cpu]
core = 9
cputype = 10
cycles = 11
blah = custom bam
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path(CONFIGS / 'dosbox' / 'dosbox.conf').read_text() == snapshot(name='config')
        assert Path(CONFIGS / 'dosbox' / 'dosbox-custom.conf').read_text() == snapshot(name='custom config')

    def test_generate_existing_rom_config(
        self, generator: DosBoxGenerator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosbox.conf',
            contents="""[foo]
bar = baz

[sdl]
output = 1
ham = spam

[cpu]
core = 2
cputype = 3
cycles = 4
blah = bam
""",
        )
        fs.create_file(
            '/userdata/roms/dos/rom.pc/dosbox.cfg',
            contents="""[foo]
bar = user baz

[sdl]
output = 5
ham = user spam

[cpu]
core = 6
cputype = 7
cycles = 8
blah = user bam
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'dos' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path(CONFIGS / 'dosbox' / 'dosbox.conf').read_text() == snapshot(name='config')
        assert Path(ROMS / 'dos' / 'rom.pc' / 'dosbox.cfg').read_text() == snapshot(name='rom config')
        assert Path(CONFIGS / 'dosbox' / 'dosbox-custom.conf').read_text() == snapshot(name='custom config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'dosbox_cpu_core': 'dynamic'},
            {'dosbox_cpu_cputype': '386'},
            {'dosbox_cpu_cycles': 'max'},
        ],
        ids=str,
    )
    def test_generate_config(
        self, generator: DosBoxGenerator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'dos' / 'rom.pc',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path(CONFIGS / 'dosbox' / 'dosbox-custom.conf').read_text() == snapshot(name='config')
