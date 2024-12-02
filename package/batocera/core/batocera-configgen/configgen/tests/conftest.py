from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

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

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion
    from syrupy.types import SerializableData


@pytest.fixture(autouse=True)
def pyudev(mocker: MockerFixture) -> Any:
    return mocker.patch.dict('sys.modules', pyudev=mocker.MagicMock())


@pytest.fixture(autouse=True)
def evdev(mocker: MockerFixture) -> Any:
    return mocker.patch.dict('sys.modules', evdev=mocker.MagicMock())


@pytest.fixture
def fs_modules_to_reload() -> list[ModuleType] | None:
    return


@pytest.fixture
def fs(fs_modules_to_reload: list[ModuleType] | None) -> Iterator[FakeFilesystem]:
    # configgen runs as root
    helpers.set_uid(0)

    with Patcher(
        additional_skip_names=['syrupy.utils', 'syrupy.extensions.amber.serializer'],
        modules_to_reload=fs_modules_to_reload,
        allow_root_user=True,
    ) as patcher:
        patcher.fs.os = OSType.LINUX  # pyright: ignore
        yield patcher.fs  # pyright: ignore

    helpers.reset_ids()


@pytest.fixture
def os_environ_lang(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
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

    return ([str(item) for item in data.array], {key: str(value) for key, value in data.env.items()})


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


_SKIP_KEYS: Final = {'PYTEST_CURRENT_TEST', 'COV_CORE_CONTEXT'}


def get_os_environ() -> dict[str, str | Path]:
    return {key: value for key, value in os.environ.items() if key not in _SKIP_KEYS}
