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


@pytest.mark.core('pocketsnes')
@pytest.mark.fallback_system_name('snes')
class TestLibretroGeneratorPocketSNES(LibretroBaseCoreTest):
    @pytest.mark.parametrize(
        ('system_name', 'files'),
        [
            ('snes-msu1', ['rom.sfc', 'README.txt', 'foo.sfc']),
            ('snes-msu1', ['rom.smc', 'README.txt', 'foo.smc']),
            ('satellaview', ['rom.sfc', 'README.txt', 'foo.sfc']),
            ('satellaview', ['rom.smc', 'README.txt', 'foo.smc']),
        ],
    )
    def test_generate_squashfs_rom(
        self,
        generator: Generator,
        files: list[str],
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        for file in files:
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
