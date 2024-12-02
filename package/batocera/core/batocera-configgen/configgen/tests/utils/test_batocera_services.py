from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from configgen.utils.batoceraServices import batoceraServices

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture


def test_get_service_status(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    mock_popen = mocker.Mock()
    mock_popen.communicate.return_value = (b'\n\t started\n\r\t  ', b'')
    subprocess_popen.return_value = mock_popen

    assert batoceraServices.getServiceStatus('my-service') == 'started'
    subprocess_popen.assert_called_once_with(
        ['batocera-services status "my-service"'], stdout=subprocess.PIPE, shell=True
    )
