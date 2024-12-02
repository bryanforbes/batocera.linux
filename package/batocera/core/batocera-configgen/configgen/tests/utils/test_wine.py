from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.utils.wine import Runner

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.fixture(autouse=True)
def fs(fs: FakeFilesystem) -> FakeFilesystem:
    fs.create_dir('/userdata/system/wine-bottles/my-bottle')

    return fs


@pytest.fixture(autouse=True)
def subprocess_popen(subprocess_popen: Mock, mocker: MockerFixture) -> Mock:
    popen_mock = mocker.Mock()
    popen_mock.communicate.return_value = (b'out', b'err')
    subprocess_popen.return_value = popen_mock
    return subprocess_popen


class TestRunner:
    def test_default(self) -> None:
        runner = Runner.default('my-bottle')

        assert Path(runner.bottle_dir) == Path('/userdata/system/wine-bottles/my-bottle')
        assert Path(runner.wine) == Path('/usr/wine/wine-tkg/lib/wine/i386-unix/wine')
        assert Path(runner.wine64) == Path('/usr/wine/wine-tkg/lib/wine/x86_64-unix/wine64')

    def test_init_tkg(self) -> None:
        runner = Runner('wine-tkg', 'my-bottle')

        assert Path(runner.bottle_dir) == Path('/userdata/system/wine-bottles/my-bottle')
        assert Path(runner.wine) == Path('/usr/wine/wine-tkg/lib/wine/i386-unix/wine')
        assert Path(runner.wine64) == Path('/usr/wine/wine-tkg/lib/wine/x86_64-unix/wine64')

    def test_init_proton(self) -> None:
        runner = Runner('wine-proton', 'my-bottle')

        assert Path(runner.bottle_dir) == Path('/userdata/system/wine-bottles/my-bottle')
        assert Path(runner.wine) == Path('/usr/wine/wine-proton/bin/wine')
        assert Path(runner.wine64) == Path('/usr/wine/wine-proton/bin/wine64')

    def test_install_wine_trick(
        self,
        subprocess_popen: Mock,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        runner = Runner('wine-tkg', 'my-bottle')

        caplog.set_level(logging.DEBUG)
        mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

        runner.install_wine_trick('some_trick')

        assert subprocess_popen.call_args_list == snapshot(name='Popen')
        assert caplog.record_tuples == snapshot(name='logging')
        assert Path('/userdata/system/wine-bottles/my-bottle/some_trick.done').exists()

    def test_install_wine_trick_environment(
        self, subprocess_popen: Mock, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        runner = Runner('wine-tkg', 'my-bottle')

        mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

        runner.install_wine_trick('some_trick', environment={'FOO': 'BAR'})

        assert subprocess_popen.call_args_list == snapshot(name='Popen')
        assert Path('/userdata/system/wine-bottles/my-bottle/some_trick.done').exists()

    def test_install_wine_trick_done_exists(self, fs: FakeFilesystem, subprocess_popen: Mock) -> None:
        runner = Runner('wine-tkg', 'my-bottle')

        fs.create_file('/userdata/system/wine-bottles/my-bottle/installed_trick.done')

        runner.install_wine_trick('installed_trick')

        subprocess_popen.assert_not_called()

    def test_regedit(
        self,
        subprocess_popen: Mock,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        runner = Runner('wine-tkg', 'my-bottle')

        caplog.set_level(logging.DEBUG)
        mocker.patch.dict('os.environ', values={'PATH': '/my/path', 'HOME': '/userdata/system'}, clear=True)

        runner.regedit(Path('/path/to/some/regedit/file.regedit'))

        assert subprocess_popen.call_args_list == snapshot(name='Popen')
        assert caplog.record_tuples == snapshot(name='logging')

    def test_get_environment(self, snapshot: SnapshotAssertion) -> None:
        assert Runner('wine-tkg', 'my-bottle').get_environment() == snapshot
