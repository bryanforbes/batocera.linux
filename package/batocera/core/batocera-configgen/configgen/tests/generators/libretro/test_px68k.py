from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('px68k')
class TestLibretroGeneratorPx68k(LibretroBaseCoreTest):
    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir('/userdata/bios/keropi')

        return fs

    @pytest.mark.parametrize_core_configs(
        [
            {'px68k_cpuspeed': '10Mhz'},
            {'px68k_ramsize': '1MB'},
            {'px68k_frameskip': '1/2 Frame'},
            {'px68k_joytype': 'CPSF-MD (8 Buttons)'},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    def test_generate_delete_files(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'x68000' / 'rom.dim')
        fs.create_file(BIOS / 'keropi' / 'config', contents='old config')
        fs.create_file(BIOS / 'keropi' / 'sram.dat', contents='old config')

        generator.generate(
            mock_system,
            ROMS / 'x68000' / 'rom.dim',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert not (BIOS / 'keropi' / 'sram.dat').exists()
        assert (BIOS / 'keropi' / 'config').read_text() == snapshot
