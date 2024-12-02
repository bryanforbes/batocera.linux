from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_lazy_fixtures import lf

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture
def fs_with_profiler_file(fs: FakeFilesystem) -> FakeFilesystem:
    fs.create_file('/var/run/emulatorlauncher.perf')
    return fs


@pytest.fixture
def cprofile_profile(mocker: MockerFixture) -> Mock:
    mock_profile = mocker.Mock()
    mocker.patch('cProfile.Profile', return_value=mock_profile)
    return mock_profile


@pytest.mark.parametrize('enabled', [None, lf('fs_with_profiler_file')])
def test_start(cprofile_profile: Mock, enabled: FakeFilesystem | None) -> None:
    import configgen.profiler

    configgen.profiler.start()

    if enabled is not None:
        cprofile_profile.enable.assert_called_once_with()
    else:
        cprofile_profile.enable.assert_not_called()


@pytest.mark.parametrize('enabled', [None, lf('fs_with_profiler_file')])
def test_stop(cprofile_profile: Mock, enabled: FakeFilesystem | None) -> None:
    import configgen.profiler

    configgen.profiler.stop()

    if enabled is not None:
        cprofile_profile.disable.assert_called_once_with()
        cprofile_profile.dump_stats.assert_called_once_with('/var/run/emulatorlauncher.prof')
    else:
        cprofile_profile.disable.assert_not_called()
        cprofile_profile.dump_stats.assert_not_called()


@pytest.mark.parametrize('enabled', [None, lf('fs_with_profiler_file')])
def test_stop_pause(cprofile_profile: Mock, enabled: FakeFilesystem | None) -> None:
    import configgen.profiler

    with configgen.profiler.pause():
        if enabled is not None:
            cprofile_profile.disable.assert_called_once_with()
        else:
            cprofile_profile.disable.assert_not_called()

        cprofile_profile.dump_stats.assert_not_called()
        cprofile_profile.enable.assert_not_called()

    cprofile_profile.dump_stats.assert_not_called()

    if enabled is not None:
        cprofile_profile.enable.assert_called_once_with()
    else:
        cprofile_profile.enable.assert_not_called()


@pytest.mark.parametrize('enabled', [None, lf('fs_with_profiler_file')])
def test_stop_pause_context_cleanup(cprofile_profile: Mock, enabled: FakeFilesystem | None) -> None:
    import configgen.profiler

    with pytest.raises(Exception, match=r'^Test exception$'), configgen.profiler.pause():  # noqa: PT012
        if enabled is not None:
            cprofile_profile.disable.assert_called_once_with()
        else:
            cprofile_profile.disable.assert_not_called()

        cprofile_profile.dump_stats.assert_not_called()
        cprofile_profile.enable.assert_not_called()

        raise Exception('Test exception')

    cprofile_profile.dump_stats.assert_not_called()
    cprofile_profile.enable.assert_not_called()
