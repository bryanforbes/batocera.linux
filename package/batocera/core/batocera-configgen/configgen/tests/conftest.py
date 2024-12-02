from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from pyfakefs import helpers
from pyfakefs.fake_filesystem import OSType
from pyfakefs.fake_filesystem_unittest import Patcher
from syrupy.extensions.amber.serializer import Repr
from syrupy.matchers import path_type

from configgen.Command import Command

if TYPE_CHECKING:
    import re
    from collections.abc import Iterator
    from types import ModuleType
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion
    from syrupy.types import SerializableData


pytest_plugins = [
    'tests.mock_controllers',
    'tests.mock_emulator',
    'tests.generators.base',
    'tests.generators.libretro.base',
]


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line('markers', 'no_fs_mods: do not modify the fake filesystem')
    config.addinivalue_line('markers', 'system_name(name): the system name to set the test to use')
    config.addinivalue_line('markers', 'emulator(name): the emulator to set the test to use')
    config.addinivalue_line('markers', 'core(name): the core to set the test to use')
    config.addinivalue_line('markers', 'mock_system_config(config): the mock system config to use')
    config.addinivalue_line('markers', 'mock_system_render_config(renderconfig): the mock system renderconfig to use')
    config.addinivalue_line('markers', 'mock_system_es_game_info(es_game_info): the mock system es_game_info to use')
    config.addinivalue_line('markers', 'parametrize_systems: mark the function to run for all core systems')
    config.addinivalue_line(
        'markers', 'parametrize_core_configs(configs, system_configs): run the function for all configs'
    )
    config.addinivalue_line('markers', 'fallback_system_name(name): the system name to use if none is provided')


@pytest.fixture(autouse=True)
def pyudev(mocker: MockerFixture) -> Mock:
    mock_pyudev = mocker.Mock()
    mocker.patch.dict('sys.modules', pyudev=mock_pyudev)
    return mock_pyudev


@pytest.fixture(autouse=True)
def evdev(mocker: MockerFixture) -> Mock:
    mock_evdev = mocker.Mock()
    mocker.patch.dict('sys.modules', **{'evdev': mock_evdev, 'evdev.ecodes': mock_evdev.ecodes})
    return mock_evdev


@pytest.fixture
def fs_modules_to_reload() -> list[ModuleType] | None:
    return


@pytest.fixture
def fs(fs_modules_to_reload: list[ModuleType] | None, monkeypatch: pytest.MonkeyPatch) -> Iterator[FakeFilesystem]:
    with monkeypatch.context() as mp:
        # delete these so our fake filesystem does not inherit the temporary directory
        # of the machine running the tests
        mp.delenv('TMP', raising=False)
        mp.delenv('TMPDIR', raising=False)
        mp.delenv('TEMP', raising=False)

        # configgen runs as root
        helpers.set_uid(0)

        with Patcher(
            additional_skip_names=[
                'syrupy.utils',
                'syrupy.extensions.amber.serializer',
                'syrupy.extensions.image',
                'syrupy.extensions.single_file',
            ],
            modules_to_reload=fs_modules_to_reload,
            allow_root_user=True,
        ) as patcher:
            patcher.fs.os = OSType.LINUX  # pyright: ignore
            yield patcher.fs  # pyright: ignore

        helpers.reset_ids()


@pytest.fixture
def os_environ_lang(request: SubRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    with monkeypatch.context() as mp:
        lang = request.param if hasattr(request, 'param') else 'en_US'

        if lang:
            mp.setenv('LANG', f'{lang}.UTF-8')
        else:
            mp.delenv('LANG', raising=False)

        yield lang


def _replace_path_types(data: Path | Command, _: re.Match[str] | None, /) -> SerializableData:
    if isinstance(data, Path):
        return Repr(f'Path({data.as_posix()!r})')

    return (
        [str(item) for item in data.array],
        {key: str(value) for key, value in data.env.items() if key not in _SKIP_KEYS},
    )


@pytest.fixture
def snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    return snapshot(
        matcher=path_type(
            types=(
                Path,
                Command,
            ),
            replacer=_replace_path_types,
        )
    )


@pytest.fixture
def subprocess_popen(mocker: MockerFixture) -> Mock:
    return mocker.patch('subprocess.Popen')


@pytest.fixture
def subprocess_run(mocker: MockerFixture) -> Mock:
    return mocker.patch('subprocess.run')


@pytest.fixture
def subprocess_call(mocker: MockerFixture) -> Mock:
    return mocker.patch('subprocess.call')


_SKIP_KEYS: Final = {'PYTEST_CURRENT_TEST', 'COV_CORE_CONTEXT'}


def get_os_environ() -> dict[str, str | Path]:
    return {key: value for key, value in os.environ.items() if key not in _SKIP_KEYS}
