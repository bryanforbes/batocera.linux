from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.exceptions import BatoceraException
from configgen.generators.Generator import Generator
from configgen.generators.importer import get_generator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture


@pytest.mark.parametrize(
    'emulator',
    [
        'abuse',
        'amiberry',
        pytest.param('applewin', marks=pytest.mark.xfail),
        'azahar',
        'bigpemu',
        'bstone',
        'cannonball',
        'catacombgl',
        'cdogs',
        'cemu',
        'cgenius',
        'citron',
        'clk',
        'corsixth',
        'devilutionx',
        'dhewm3',
        'dolphin',
        'dolphin_triforce',
        'dosbox',
        'dosbox_staging',
        'dosboxx',
        'drastic',
        'duckstation',
        'dxx-rebirth',
        'easyrpg',
        'ecwolf',
        'eduke32',
        'etlegacy',
        'fallout1-ce',
        'fallout2-ce',
        'fba2x',
        'flatpak',
        'flycast',
        'fsuae',
        'gsplus',
        'gzdoom',
        'hatari',
        'hcl',
        'hurrican',
        'hypseus-singe',
        'ikemen',
        'ioquake3',
        'iortcw',
        'jazz2-native',
        'libretro',
        'lightspark',
        'lindbergh-loader',
        'mame',
        'melonds',
        'model2emu',
        'moonlight',
        'mugen',
        'mupen64plus',
        'odcommander',
        'openbor',
        'openjazz',
        'openjk',
        'openjkdf2',
        'openmohaa',
        'openmsx',
        'pcsx2',
        'play',
        'ppsspp',
        'pygame',
        'pyxel',
        'raze',
        'redream',
        'rpcs3',
        'ruffle',
        'ryujinx',
        'samcoupe',
        'scummvm',
        'sdlpop',
        'sh',
        'shadps4',
        'solarus',
        'sonic-mania',
        'sonic2013',
        'sonic3-air',
        'soniccd',
        'steam',
        'stella',
        'supermodel',
        'taradino',
        'theforceengine',
        'thextech',
        'tsugaru',
        'tyrian',
        'uqm',
        'vice',
        'vita3k',
        'vpinball',
        'wine',
        'x16emu',
        'xash3d_fwgs',
        'xemu',
        'xenia',
        'xenia-canary',
    ],
)
def test_get_generator(emulator: str) -> None:
    assert isinstance(get_generator(emulator), Generator)


def test_get_generator_missing() -> None:
    with pytest.raises(BatoceraException, match=r'^No generator found for emulator foo$'):
        get_generator('foo')


def test_get_generator_import_error(mocker: MockerFixture) -> None:
    mocker.patch('configgen.generators.importer.import_module', side_effect=ImportError())

    with pytest.raises(BatoceraException, match=r'^Error importing generator for emulator foo$'):
        get_generator('foo')


def test_get_generator_no_generator_class(mocker: MockerFixture) -> None:
    mocker.patch('configgen.generators.importer.import_module', side_effect=AttributeError())

    with pytest.raises(BatoceraException, match=r'^No generator found for emulator foo'):
        get_generator('foo')
