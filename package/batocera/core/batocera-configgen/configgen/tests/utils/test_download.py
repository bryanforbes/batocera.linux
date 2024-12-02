from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.utils.download import DownloadException, download

if TYPE_CHECKING:
    from collections.abc import Iterator
    from unittest.mock import Mock

    from pytest_mock import MockerFixture

pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture
def download_contents() -> bytes:
    return b''


@pytest.fixture
def download_response(mocker: MockerFixture, download_contents: bytes) -> Mock:
    content = io.BytesIO(download_contents)

    def side_effect(chunk_size: int = -1) -> Iterator[bytes]:
        while chunk := content.read(chunk_size):
            yield chunk

    response = mocker.MagicMock()
    response.iter_content.side_effect = side_effect
    response.__enter__.return_value = response
    return response


@pytest.fixture(autouse=True)
def requests_get(mocker: MockerFixture, download_response: Mock) -> Mock:
    return mocker.patch('requests.get', return_value=download_response)


@pytest.mark.parametrize('download_contents', [b'', b'asdf' * 8192], ids=['no content', 'big content'])
def test_download(download_contents: bytes) -> None:
    with download('http://example.com/foo.zip', Path('/tmp')) as file:
        assert Path(file.name).read_bytes() == download_contents

    assert not Path(file.name).exists()


def test_download_raises(download_response: Mock) -> None:
    download_response.raise_for_status.side_effect = Exception('Test exception')

    with (
        pytest.raises(Exception, match=r'^Test exception$') as excinfo,
        download('http://example.com/foo.zip', Path('/tmp')) as _,
    ):
        pass

    assert not isinstance(excinfo.value, DownloadException)


def test_download_raises_requests_errors(download_response: Mock) -> None:
    import requests

    download_response.raise_for_status.side_effect = requests.RequestException

    with pytest.raises(DownloadException) as excinfo, download('http://example.com/foo.zip', Path('/tmp')) as _:
        pass

    assert isinstance(excinfo.value.__cause__, requests.RequestException)


def test_download_cleanup() -> None:
    with (  # noqa: PT012
        pytest.raises(Exception, match=r'^Test exception$'),
        download('http://example.com/foo.zip', Path('/tmp')) as file,
    ):
        assert Path(file.name).exists()
        raise Exception('Test exception')

    assert not Path(file.name).exists()
