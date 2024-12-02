from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('genesisplusgx-wide')
@pytest.mark.fallback_system_name('megadrive')
class TestLibretroGeneratorGenesisPlusGXWide(LibretroBaseCoreTest):
    @pytest.mark.system_name('msu-md')
    def test_generate_squashfs_rom(
        self, generator: Generator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        for file in ['rom.md', 'README.txt', 'foo.md']:
            fs.create_file(f'/var/run/squashfs/rom_name/{file}')

        assert (
            generator.generate(
                mock_system,
                Path('/var/run/squashfs/rom_name'),
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
