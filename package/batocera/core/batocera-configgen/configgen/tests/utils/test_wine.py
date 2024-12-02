from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.utils.wine import get_wine_environment, install_wine_trick, regedit

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.fixture(autouse=True)
def fs(fs: FakeFilesystem) -> FakeFilesystem:
    fs.create_dir('/path/to/wine/prefix')

    return fs


@pytest.fixture(autouse=True)
def subprocess_popen(mocker: MockerFixture) -> Mock:
    popen_mock = mocker.Mock()
    Popen = mocker.patch('subprocess.Popen', return_value=popen_mock)
    popen_mock.communicate.return_value = (b'out', b'err')
    return Popen


def test_install_wine_trick(
    subprocess_popen: Mock, mocker: MockerFixture, snapshot: SnapshotAssertion, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

    install_wine_trick(Path('/path/to/wine/prefix'), 'some_trick')

    assert subprocess_popen.call_args_list == snapshot(name='Popen')
    assert caplog.record_tuples == snapshot(name='logging')
    assert Path('/path/to/wine/prefix/some_trick.done').exists()


def test_install_wine_trick_environment(
    subprocess_popen: Mock, mocker: MockerFixture, snapshot: SnapshotAssertion
) -> None:
    mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

    install_wine_trick(Path('/path/to/wine/prefix'), 'some_trick', environment={'FOO': 'BAR'})

    assert subprocess_popen.call_args_list == snapshot(name='Popen')
    assert Path('/path/to/wine/prefix/some_trick.done').exists()


def test_install_wine_trick_done_exists(fs: FakeFilesystem, subprocess_popen: Mock) -> None:
    fs.create_file('/path/to/wine/prefix/installed_trick.done')

    install_wine_trick(Path('/path/to/wine/prefix'), 'installed_trick')

    subprocess_popen.assert_not_called()


def test_regedit(
    subprocess_popen: Mock, mocker: MockerFixture, snapshot: SnapshotAssertion, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

    regedit(Path('/path/to/wine/prefix'), Path('/path/to/some/regedit/file.regedit'))

    assert subprocess_popen.call_args_list == snapshot(name='Popen')
    assert caplog.record_tuples == snapshot(name='logging')


def test_get_wine_environment(snapshot: SnapshotAssertion) -> None:
    assert get_wine_environment(Path('/my/wine/prefix')) == snapshot
