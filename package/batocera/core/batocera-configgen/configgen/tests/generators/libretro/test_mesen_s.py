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


@pytest.mark.core('mesen-s')
@pytest.mark.fallback_system_name('snes')
class TestLibretroGeneratorMesenS(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'mesen-s_ntsc_filter': 'Composite (Blargg)'},
            {'mesen-s_blend_high_res': 'enabled'},
            {'mesen-s_cubic_interpolation': 'enabled'},
            {'mesen-s_sgb2': 'disabled'},
            {'mesen-s_overclock': 'Low'},
            {'mesen-s_overclock_type': 'After NMI'},
            {'mesen-s_superfx_overclock': '200%'},
        ],
        {
            'snes': [{'mesen-s_gbmodel': 'Game Boy'}],
            'gb': [{'mesen-s_gbmodel': 'Game Boy Color'}],
            'gbc': [{'mesen-s_gbmodel': 'Game Boy'}],
            'sgb': [{'mesen-s_gbmodel': 'Game Boy'}],
            'satellaview': [{'mesen-s_gbmodel': 'Game Boy'}],
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize(
        ('system_name', 'files'),
        [
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
