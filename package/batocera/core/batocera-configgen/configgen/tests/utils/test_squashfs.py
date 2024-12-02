from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.exceptions import BatoceraException
from configgen.utils.squashfs import squashfs_rom

if TYPE_CHECKING:
    from types import ModuleType
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion


pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture
def fs_modules_to_reload() -> list[ModuleType]:
    from configgen.utils import squashfs

    return [squashfs]


@pytest.fixture(autouse=True)
def subprocess_call(subprocess_call: Mock) -> Mock:
    subprocess_call.return_value = 0
    return subprocess_call


def test_squashfs_rom(subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    input_rom = Path('/path/to/rom-name.squashfs')

    with squashfs_rom(input_rom) as rom:
        assert rom == Path('/var/run/squashfs/rom-name')
        assert Path('/var/run/squashfs/rom-name').is_dir()

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_context_raises(subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    input_rom = Path('/path/to/rom-name.squashfs')

    with pytest.raises(Exception, match=r'^test exception$'), squashfs_rom(input_rom):
        raise Exception('test exception')

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_single_file(fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'mount':
            fs.create_file('/var/run/squashfs/rom-name/rom-name')

        if args[0] == 'umount':
            fs.remove('/var/run/squashfs/rom-name/rom-name')

        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with squashfs_rom(input_rom) as rom:
        assert rom == Path('/var/run/squashfs/rom-name/rom-name')

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_single_file_context_raises(
    fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion
) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'mount':
            fs.create_file('/var/run/squashfs/rom-name/rom-name')

        if args[0] == 'umount':
            fs.remove('/var/run/squashfs/rom-name/rom-name')

        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with pytest.raises(Exception, match=r'^test exception$'), squashfs_rom(input_rom):
        raise Exception('test exception')

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_linked(fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'mount':
            fs.create_file('/var/run/squashfs/rom-name/actual-rom')
            fs.create_symlink('/var/run/squashfs/rom-name/.ROM', '/var/run/squashfs/rom-name/actual-rom')

        if args[0] == 'umount':
            fs.remove('/var/run/squashfs/rom-name/.ROM')
            fs.remove('/var/run/squashfs/rom-name/actual-rom')

        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with squashfs_rom(input_rom) as rom:
        assert rom == Path('/var/run/squashfs/rom-name/actual-rom')

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_linked_context_raises(
    fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion
) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'mount':
            fs.create_file('/var/run/squashfs/rom-name/actual-rom')
            fs.create_symlink('/var/run/squashfs/rom-name/.ROM', '/var/run/squashfs/rom-name/actual-rom')

        if args[0] == 'umount':
            fs.remove('/var/run/squashfs/rom-name/.ROM')
            fs.remove('/var/run/squashfs/rom-name/actual-rom')

        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with pytest.raises(Exception, match=r'^test exception$'), squashfs_rom(input_rom):
        raise Exception('test exception')

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_mount_fails(subprocess_call: Mock) -> None:
    subprocess_call.return_value = 1

    input_rom = Path('/path/to/rom-name.squashfs')

    with (
        pytest.raises(BatoceraException, match=r'^Unable to mount the file /path/to/rom-name.squashfs'),
        squashfs_rom(input_rom),
    ):
        pass


def test_squashfs_rom_mount_fails_rmdir_fails(fs: FakeFilesystem, subprocess_call: Mock) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'mount':
            fs.create_file('/var/run/squashfs/rom-name/foo')
            return 1
        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with (
        pytest.raises(BatoceraException, match=r'^Unable to mount the file /path/to/rom-name.squashfs'),
        squashfs_rom(input_rom),
    ):
        pass


def test_squashfs_rom_umount_fails(subprocess_call: Mock) -> None:
    def side_effect(args: list[str | Path]) -> int:
        if args[0] == 'umount':
            return 1
        return 0

    subprocess_call.side_effect = side_effect

    input_rom = Path('/path/to/rom-name.squashfs')

    with (
        pytest.raises(BatoceraException, match=r'^Unable to unmount the file /var/run/squashfs/rom-name'),
        squashfs_rom(input_rom),
    ):
        pass


def test_squashfs_rom_existing(fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    fs.create_dir('/var/run/squashfs/rom-name')

    input_rom = Path('/path/to/rom-name.squashfs')

    with squashfs_rom(input_rom) as rom:
        assert rom == Path('/var/run/squashfs/rom-name')
        assert Path('/var/run/squashfs/rom-name').is_dir()

    assert not Path('/var/run/squashfs/rom-name').exists()
    assert subprocess_call.call_args_list == snapshot(name='calls')


def test_squashfs_rom_existing_rmdir_fails(fs: FakeFilesystem, subprocess_call: Mock) -> None:
    fs.create_file('/var/run/squashfs/rom-name/something')

    input_rom = Path('/path/to/rom-name.squashfs')

    with squashfs_rom(input_rom) as rom:
        assert rom == Path('/var/run/squashfs/rom-name')

    assert Path('/var/run/squashfs/rom-name').exists()
    subprocess_call.assert_not_called()
