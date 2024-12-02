from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest, parametrize_guns

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('bsnes')
@pytest.mark.fallback_system_name('snes')
class TestLibretroGeneratorBsnes(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'bsnes_video_filter': 'NTSC (RF)'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @parametrize_guns(metadata=[{'gun_type': 'justifier'}, {'gun_reversedbuttons': 'true'}])
    def test_generate_guns(
        self, mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
    ) -> None:
        return super().test_generate_guns(
            mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
        )

    @pytest.mark.parametrize(
        ('system_name', 'files'),
        [
            ('snes-msu1', ['rom.sfc', 'README.txt', 'foo.sfc']),
            ('snes-msu1', ['rom.smc', 'README.txt', 'foo.smc']),
            ('sgb-msu1', ['rom.gb', 'README.txt', 'foo.gb']),
            ('sgb-msu1', ['rom.gbc', 'README.txt', 'foo.gbc']),
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
