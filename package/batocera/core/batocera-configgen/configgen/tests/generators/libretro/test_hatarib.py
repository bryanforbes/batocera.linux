from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.generators.libretro.utils import (
    get_configs_with_base,
    get_extensions_iter,
)

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('hatarib')
class TestLibretroGeneratorHatarib(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'hatarib_machine': '1'},
            {'hatarib_cpu': '1'},
            {'hatarib_cpu_clock': '8'},
            {'hatarib_memory': '2048'},
            {'hatarib_ratio': '1'},
            {'hatarib_borders': '1'},
            {'hatarib_pause': '3'},
            {'hatarib_language': '0'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='hatari.cfg')

    @pytest.mark.parametrize(
        'mock_system_config',
        get_configs_with_base({}, [('hatarib_drive', ['IDE', 'ACSI'])]),
        ids=str,
    )
    @pytest.mark.parametrize('extension', get_extensions_iter('hatarib'))
    def test_generate_rom_extension(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        extension: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'atarist' / f'rom.{extension}')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / f'rom.{extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        self.assert_core_config_matches(snapshot)
        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='hatari.cfg')

        assert (BIOS / 'hatarib').is_dir()
        if extension in ['hd', 'gemdos']:
            assert Path(BIOS / 'hatarib' / 'hdd').resolve() == Path(f'/userdata/roms/atarist/rom.{extension}')
        else:
            assert not (BIOS / 'hatarib' / 'hdd').exists()

    @pytest.mark.parametrize('extension', get_extensions_iter('hatarib'))
    def test_generate_existing_symlink(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        extension: str,
        mock_system: Emulator,
    ) -> None:
        fs.create_file(ROMS / 'atarist' / f'rom.{extension}')
        fs.create_file('/tmp/foo')
        fs.create_symlink(BIOS / 'hatarib' / 'hdd', '/tmp/foo')

        generator.generate(
            mock_system,
            ROMS / 'atarist' / f'rom.{extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        if extension in ['hd', 'gemdos']:
            assert Path(BIOS / 'hatarib' / 'hdd').resolve() == Path(f'/userdata/roms/atarist/rom.{extension}')
        else:
            assert not (BIOS / 'hatarib' / 'hdd').exists()

    def test_generate_existing_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'atarist' / 'rom.zip')
        fs.create_file(
            CONFIGS / 'hatari' / 'hatari.cfg',
            contents="""[Joystick1]
nJoyId = 1

[Log]
bConfirmQuit = TRUE

[Screen]
bShowStatusbar = TRUE

[Foo]
bBar = FALSE
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'atarist' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot
