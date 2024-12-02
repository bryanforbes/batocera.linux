from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.utils import buildargs

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion


def test_parse_args(fs: FakeFilesystem, snapshot: SnapshotAssertion) -> None:
    fs.create_file('/userdata/roms/eduke32/duke/DUKE3D.GRP')
    fs.create_file('/userdata/roms/eduke32/duke/duke3d_hrp.zip')
    fs.create_file('/userdata/roms/eduke32/duke/duke3d_music-sc55.zip')
    fs.create_file('/userdata/roms/eduke32/mod/mod.con')
    fs.create_file('/userdata/roms/eduke32/mod/mod2.con')
    fs.create_file('/userdata/roms/eduke32/mod/mod3.con')
    fs.create_file('/userdata/roms/eduke32/mod/mod.def')
    fs.create_file('/userdata/roms/eduke32/mod/mod2.def')
    fs.create_file('/userdata/roms/eduke32/mod/mod3.def')
    fs.create_file('/userdata/roms/eduke32/mod/mod.map')
    fs.create_file(
        '/userdata/roms/eduke32/rom.eduke32',
        contents="""# A comment
// Another comment
FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
FILE+ = /duke/duke3d_music-sc55.zip
FILE+ = foo
CON = /mod/mod.con
CON+ = /mod/mod2.con
CON+ = /mod/mod3.con
DEF = /mod/mod.def
DEF+ = /mod/mod2.def
DEF+ = /mod/mod3.def
DIR = /duke
DIR = /mod
MAP = /mod/mod.map
""",
    )

    args: list[str | Path] = []
    result = buildargs.parse_args(args, Path('/userdata/roms/eduke32/rom.eduke32'))

    assert result.okay
    assert args == snapshot


@pytest.mark.parametrize(
    'contents',
    [
        'FILE',
        'FILE =',
        'FILE = foo = bar',
        'SPAM = ham',
        'FILE = /duke/blah.grp',
        'FILE = /duke/DUKE3D.GRP\nFILE = /duke/duke3d_hrp.zip',
        """FILE = /duke/DUKE3D.GRP
FILE = /duke/duke3d_hrp.zip
FILE+ = /duke/blah.grp
SPAM = ham
CON =
DIR""",
    ],
)
def test_parse_args_errors(fs: FakeFilesystem, contents: str, snapshot: SnapshotAssertion) -> None:
    fs.create_file('/userdata/roms/eduke32/duke/DUKE3D.GRP')
    fs.create_file('/userdata/roms/eduke32/duke/duke3d_hrp.zip')
    fs.create_file('/userdata/roms/eduke32/rom.eduke32', contents=contents)

    args: list[str | Path] = []
    result = buildargs.parse_args(args, Path('/userdata/roms/eduke32/rom.eduke32'))

    assert not result.okay
    assert args == snapshot(name='args')
    assert result.message == snapshot(name='message')
