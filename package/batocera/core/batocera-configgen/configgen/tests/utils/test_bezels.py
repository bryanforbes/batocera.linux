from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from configgen.batoceraPaths import ROMS
from configgen.utils.bezels import fast_image_size, getBezelInfos, gunBordersSize, gunsBordersColorFomConfig

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


pytestmark = pytest.mark.usefixtures('fs')


@pytest.mark.parametrize('alt_decoration', [0, '90'])
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


@pytest.mark.parametrize('borders_color', ['red', 'green', 'blue', 'white', 'magenta', None])
def test_guns_borders_color_from_config(borders_color: str | None, snapshot: SnapshotAssertion) -> None:
    assert (
        gunsBordersColorFomConfig({} if borders_color is None else {'controllers.guns.borderscolor': borders_color})
        == snapshot
    )


@pytest.mark.parametrize('borders_size', ['thin', 'medium', 'big', 'huge'])
def test_gun_borders_size(borders_size: str, snapshot: SnapshotAssertion) -> None:
    assert gunBordersSize(borders_size) == snapshot


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
