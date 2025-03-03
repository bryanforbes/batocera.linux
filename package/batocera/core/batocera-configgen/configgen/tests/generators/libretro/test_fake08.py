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


@pytest.mark.core('fake08')
class TestLibretroGeneratorFake08(LibretroBaseCoreTest):
    def test_generate_m3u(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'pico8' / 'rom.m3u',
            contents="""rom_file1.p8
rom_file2.p8
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'pico8' / 'rom.m3u',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
