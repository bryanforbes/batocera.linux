from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('boom3')
class TestLibretroGeneratorBoom3(LibretroBaseCoreTest):
    @pytest.mark.parametrize('subdirectory', ['base', 'd3xp'])
    def test_generate_subdir(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        subdirectory: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'doom3' / 'rom.d3', contents=f'{subdirectory}/pak000.pk4\nfoo')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'doom3' / 'rom.d3',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
