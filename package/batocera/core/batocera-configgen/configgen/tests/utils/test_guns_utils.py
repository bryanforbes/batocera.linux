from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BATOCERA_SHARE_DIR, CONFIGS, ROMS, SAVES
from configgen.utils.gunsUtils import precalibration

if TYPE_CHECKING:
    from _typeshed import StrPath

    from pyfakefs.fake_filesystem import FakeFilesystem

pytestmark = pytest.mark.usefixtures('fs')


@pytest.mark.parametrize(
    'source_files',
    [
        None,
        ['rom.zip.nvmem'],
        ['rom.zip.nvmem', 'rom.zip.nvmem2'],
    ],
)
def test_precalibration_atomiswave(fs: FakeFilesystem, source_files: list[StrPath] | None) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'atomiswave')

    if source_files:
        for file in source_files:
            fs.create_file(
                BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'atomiswave' / 'reicast' / file,
                contents=f'source file {file}',
            )

    precalibration('atomiswave', 'flycast', 'flycast', ROMS / 'atomiswave' / 'rom.zip')

    if not source_files:
        assert not SAVES.exists()
        assert not CONFIGS.exists()
    else:
        for file in source_files:
            assert SAVES / 'atomiswave' / 'reicast' / file


@pytest.mark.parametrize(
    'source_files',
    [
        None,
        ['rom.zip.nvmem'],
        ['rom.zip.nvmem', 'rom.zip.nvmem2'],
    ],
)
def test_precalibration_naomi(fs: FakeFilesystem, source_files: list[StrPath] | None) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'naomi')

    if source_files:
        for file in source_files:
            fs.create_file(
                BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'naomi' / 'reicast' / file,
                contents=f'source file {file}',
            )

    precalibration('naomi', 'reicast', 'reicast', ROMS / 'naomi' / 'rom.zip')

    if not source_files:
        assert not SAVES.exists()
        assert not CONFIGS.exists()
    else:
        for file in source_files:
            assert SAVES / 'naomi' / 'reicast' / file


def test_precalibration_model2(fs: FakeFilesystem) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'model2')

    precalibration('model2', 'reicast', 'reicast', ROMS / 'model2' / 'rom.zip')

    assert not (SAVES / 'model2' / 'NVDATA' / 'rom.zip.DAT').exists()

    fs.create_file(
        BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'model2' / 'NVDATA' / 'rom.zip.DAT',
        contents='source file',
    )

    precalibration('model2', 'reicast', 'reicast', ROMS / 'model2' / 'rom.zip')
    assert (SAVES / 'model2' / 'NVDATA' / 'rom.zip.DAT').read_text() == 'source file'


def test_precalibration_supermodel(fs: FakeFilesystem) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'supermodel')

    precalibration('supermodel', 'reicast', 'reicast', ROMS / 'supermodel' / 'rom.zip')

    assert not (SAVES / 'supermodel' / 'NVDATA' / 'rom.nv').exists()

    fs.create_file(
        BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'supermodel' / 'NVDATA' / 'rom.nv',
        contents='source file',
    )

    precalibration('supermodel', 'reicast', 'reicast', ROMS / 'supermodel' / 'rom.zip')
    assert (SAVES / 'supermodel' / 'NVDATA' / 'rom.nv').read_text() == 'source file'


def test_precalibration_namco2x6(fs: FakeFilesystem) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'namco2x6')

    precalibration('namco2x6', 'reicast', 'reicast', ROMS / 'namco2x6' / 'rom.zip')
    assert not (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').exists()

    precalibration('namco2x6', 'play', 'play', ROMS / 'namco2x6' / 'rom.zip')
    assert not (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').exists()

    fs.create_file(
        BATOCERA_SHARE_DIR / 'guns-precalibrations' / 'namco2x6' / 'play' / 'rom',
        contents='source file',
    )

    precalibration('namco2x6', 'play', 'play', ROMS / 'namco2x6' / 'rom.zip')
    assert (CONFIGS / 'play' / 'Play Data Files' / 'arcadesaves' / 'rom.backupram').read_text() == 'source file'


def test_precalibration_no_source() -> None:
    precalibration('atomiswave', 'reicast', 'reicast', ROMS / 'atomiswave' / 'rom.zip')

    assert not (SAVES / 'atomiswave' / 'reicast' / 'rom.zip.nvmem').exists()
    assert not (SAVES / 'atomiswave' / 'reicast' / 'rom.zip.nvmem2').exists()


def test_precalibration_no_system(fs: FakeFilesystem) -> None:
    fs.create_dir(BATOCERA_SHARE_DIR / 'guns-precalibrations' / '3ds')

    precalibration('3ds', 'reicast', 'reicast', ROMS / 'atomiswave' / 'rom.zip')

    assert not SAVES.exists()
    assert not CONFIGS.exists()
