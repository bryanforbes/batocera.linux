from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from pyfakefs.fake_filesystem import OSType
from pyfakefs.fake_filesystem_unittest import Patcher

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture


@pytest.fixture(autouse=True)
def pyudev(mocker: MockerFixture) -> Any:
    return mocker.patch.dict('sys.modules', pyudev=mocker.MagicMock())


@pytest.fixture(autouse=True)
def evdev(mocker: MockerFixture) -> Any:
    return mocker.patch.dict('sys.modules', evdev=mocker.MagicMock())


@pytest.fixture
def fs() -> Iterator[FakeFilesystem]:
    with Patcher(additional_skip_names=['syrupy.utils', 'syrupy.extensions.amber.serializer']) as patcher:
        patcher.fs.os = OSType.LINUX  # pyright: ignore
        yield patcher.fs  # pyright: ignore


@pytest.fixture
def os_environ_lang(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> Iterator[str]:
    with monkeypatch.context() as mp:
        lang = request.param if hasattr(request, 'param') else 'en_US'

        if lang:
            mp.setenv('LANG', f'{lang}.UTF-8')
        else:
            mp.delenv('LANG', raising=False)

        yield lang
