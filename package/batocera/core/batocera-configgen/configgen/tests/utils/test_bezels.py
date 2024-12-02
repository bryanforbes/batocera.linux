from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from PIL import Image, UnidentifiedImageError
from syrupy.extensions.image import PNGImageSnapshotExtension

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.utils.bezels import (
    createTransparentBezel,
    fast_image_size,
    getBezelInfos,
    gunBorderImage,
    gunBordersSize,
    gunsBordersColorFomConfig,
    resizeImage,
    tatooImage,
)
from tests.mock_emulator import MockEmulator

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture
def image_open(mocker: MockerFixture) -> Mock:
    return mocker.patch('PIL.Image.open')


@pytest.mark.parametrize('alt_decoration', ['0', '90'])
def test_get_bezel_infos(
    alt_decoration: int | str, mocker: MockerFixture, fs: FakeFilesystem, snapshot: SnapshotAssertion
) -> None:
    mocker.patch('configgen.utils.bezels.getAltDecoration', return_value=alt_decoration)

    assert getBezelInfos(ROMS / 'dreamcast' / 'rom to run.chd', 'arcade_1980s', 'dreamcast', 'flycast') == snapshot

    paths = [
        '/userdata/decorations/arcade_1980s/games/dreamcast/rom to run.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/games/dreamcast/rom to run.png',
        '/userdata/decorations/arcade_1980s/games/rom to run.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/games/rom to run.png',
        '/userdata/decorations/arcade_1980s/systems/dreamcast-90.png',
        '/userdata/decorations/arcade_1980s/systems/dreamcast.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/systems/dreamcast-90.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/systems/dreamcast.png',
        '/userdata/decorations/arcade_1980s/default-90.png',
        '/userdata/decorations/arcade_1980s/default.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/default-90.png',
        '/usr/share/batocera/datainit/decorations/arcade_1980s/default.png',
    ]

    for path in paths:
        fs.create_file(path)

    for path in paths:
        assert getBezelInfos(ROMS / 'dreamcast' / 'rom to run.chd', 'arcade_1980s', 'dreamcast', 'flycast') == snapshot(
            name=path
        )
        fs.remove(path)


@pytest.mark.parametrize('size', [(1, 1), (2, 2), (1920, 1080)])
def test_fast_image_size(size: tuple[int, int]) -> None:
    img = Image.new('RGBA', size)
    img.save('/tmp/test.png', format='PNG')

    assert fast_image_size('/tmp/test.png') == size


def test_fast_image_size_errors(fs: FakeFilesystem) -> None:
    assert fast_image_size('/tmp/test.png') == (-1, -1)

    fs.create_file('/tmp/test.png')
    assert fast_image_size('/tmp/test.png') == (-1, -1)

    Path('/tmp/test.png').write_bytes(''.join(str(n) for n in range(32)).encode())
    assert fast_image_size('/tmp/test.png') == (-1, -1)


@pytest.mark.parametrize('rgba', [False, True])
@pytest.mark.parametrize('stretch', [False, True], ids=['no stretch', 'stretch'])
@pytest.mark.parametrize(
    'size',
    [
        (640, 480),
        (1280, 720),
        (1920, 1440),
        (1920, 1080),
        (2048, 1536),
        (2048, 1152),
    ],
    ids=str,
)
def test_resize_image(
    fs: FakeFilesystem, snapshot: SnapshotAssertion, size: tuple[int, int], stretch: bool, rgba: bool
) -> None:
    if rgba:
        createTransparentBezel(Path('/tmp/dreamcast.png'), 1920, 1080)
    else:
        fs.add_real_file(
            Path(__file__).parent / '__files__' / 'bezels' / 'dreamcast.png', target_path='/tmp/dreamcast.png'
        )

    resizeImage('/tmp/dreamcast.png', '/tmp/resized.png', size[0], size[1], stretch)

    assert Path('/tmp/resized.png').read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension)


@pytest.mark.parametrize('corner', [None, 'NW', 'NE', 'SE', 'SW'])
@pytest.mark.parametrize(
    ('bezel_tattoo', 'system_name', 'tattoo_file'),
    [
        (None, 'dreamcast', None),
        ('system', 'dreamcast', None),
        ('system', 'unknown', None),
        ('custom', 'dreamcast', 'missing'),
        ('custom', 'dreamcast', 'snes'),
    ],
    ids=str,
)
def test_tatoo_image(
    fs: FakeFilesystem,
    system_name: str,
    bezel_tattoo: str | None,
    corner: str | None,
    tattoo_file: str | None,
    snapshot: SnapshotAssertion,
) -> None:
    fs.add_real_directory(
        Path(__file__).parent / '__files__' / 'controller-overlays',
        target_path='/usr/share/batocera/controller-overlays',
    )

    input = Path('/tmp/input.png')
    output = Path('/tmp/tattoo.png')

    createTransparentBezel(input, 1280, 720)

    mock_system = MockEmulator(system_name, {'bezel.tattoo': bezel_tattoo or 'none'})

    if tattoo_file:
        mock_system.config['bezel.tattoo_file'] = (
            f'/tmp/{tattoo_file}.png'
            if tattoo_file == 'missing'
            else f'/usr/share/batocera/controller-overlays/{tattoo_file}.png'
        )

    if corner is not None:
        mock_system.config['bezel.tattoo_corner'] = corner

    tatooImage(input, output, cast('Emulator', mock_system))

    assert output.read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension)


@pytest.mark.parametrize('size_spec', [None, 'width', 'height'])
@pytest.mark.parametrize('corner', ['NW', 'NE', 'SE', 'SW'])
@pytest.mark.parametrize(
    ('bezel_tattoo', 'tattoo_file'),
    [
        (None, None),
        ('system', None),
        ('custom', 'snes'),
    ],
    ids=str,
)
def test_tatoo_image_no_resize(
    fs: FakeFilesystem,
    bezel_tattoo: str | None,
    tattoo_file: str | None,
    corner: str | None,
    size_spec: str | None,
    snapshot: SnapshotAssertion,
) -> None:
    fs.add_real_directory(
        Path(__file__).parent / '__files__' / 'controller-overlays',
        target_path='/usr/share/batocera/controller-overlays',
    )

    input = Path('/tmp/input.png')
    output = Path('/tmp/tattoo.png')

    size: tuple[int, int] = (356, 267) if size_spec == 'height' else (224, 168) if size_spec == 'width' else (1280, 720)
    createTransparentBezel(input, *size)

    mock_system = MockEmulator('dreamcast', {'bezel.tattoo': bezel_tattoo or 'none', 'bezel.resize_tattoo': '0'})

    if tattoo_file:
        mock_system.config['bezel.tattoo_file'] = f'/usr/share/batocera/controller-overlays/{tattoo_file}.png'

    if corner is not None:
        mock_system.config['bezel.tattoo_corner'] = corner

    tatooImage(input, output, cast('Emulator', mock_system))

    assert output.read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension)


@pytest.mark.parametrize(
    ('bezel_tattoo', 'tattoo_file'),
    [
        (None, None),
        ('system', None),
        ('custom', 'snes'),
    ],
    ids=str,
)
def test_tatoo_image_raises(
    fs: FakeFilesystem,
    mocker: MockerFixture,
    bezel_tattoo: str | None,
    tattoo_file: str | None,
    image_open: Mock,
) -> None:
    image_open.side_effect = [UnidentifiedImageError('Test exception'), mocker.Mock()]

    fs.add_real_directory(
        Path(__file__).parent / '__files__' / 'controller-overlays',
        target_path='/usr/share/batocera/controller-overlays',
    )

    input = Path('/tmp/input.png')
    output = Path('/tmp/tattoo.png')

    mock_system = MockEmulator('dreamcast', {'bezel.tattoo': bezel_tattoo or 'none'})

    if tattoo_file:
        mock_system.config['bezel.tattoo_file'] = f'/usr/share/batocera/controller-overlays/{tattoo_file}.png'

    with pytest.raises(BatoceraException, match=r'^Tattoo image could not be opened: \/'):
        tatooImage(input, output, cast('Emulator', mock_system))


@pytest.mark.parametrize('borders_size', ['thin', 'medium', 'big', 'huge'])
def test_gun_borders_size(borders_size: str, snapshot: SnapshotAssertion) -> None:
    assert gunBordersSize(borders_size) == snapshot


@pytest.mark.parametrize('aspect_ratio', [None, '4:3'])
@pytest.mark.parametrize(
    ('inner_size', 'outer_size'),
    [
        (1, 0),  # thin
        (2, 0),  # medium
        (2, 1),  # big
        (0, 0),  # default
    ],
)
@pytest.mark.parametrize(('image_width', 'image_height'), [(1280, 720), (1024, 768)], ids=str)
def test_gun_border_image(
    image_width: int,
    image_height: int,
    inner_size: int,
    outer_size: int,
    aspect_ratio: str | None,
    snapshot: SnapshotAssertion,
) -> None:
    input = Path('/tmp/input.png')
    output = Path('/tmp/output.png')
    createTransparentBezel(input, image_width, image_height)

    assert gunBorderImage(input, output, aspect_ratio, inner_size, outer_size, '#0000ff', '#00ff00') == snapshot
    assert output.read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension, name='image')


@pytest.mark.parametrize('borders_color', ['red', 'green', 'blue', 'white', 'magenta', None])
def test_guns_borders_color_from_config(borders_color: str | None, snapshot: SnapshotAssertion) -> None:
    assert (
        gunsBordersColorFomConfig(
            SystemConfig({} if borders_color is None else {'controllers.guns.borderscolor': borders_color})
        )
        == snapshot
    )


@pytest.mark.parametrize('size', [(1, 1), (2, 2), (1920, 1080)], ids=str)
def test_create_transparent_bezel(size: tuple[int, int], snapshot: SnapshotAssertion) -> None:
    createTransparentBezel(Path('/tmp/test.png'), *size)

    assert Path('/tmp/test.png').read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension)
