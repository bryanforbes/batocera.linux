from __future__ import annotations

from subprocess import CalledProcessError
from typing import TYPE_CHECKING

import pytest

from configgen.utils.vulkan import (
    get_discrete_gpu_index,
    get_discrete_gpu_name,
    get_discrete_gpu_uuid,
    get_version,
    has_discrete_gpu,
    is_available,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.fixture(autouse=True)
def subprocess_check_output(mocker: MockerFixture) -> Mock:
    return mocker.patch('subprocess.check_output')


@pytest.mark.parametrize(('return_value', 'expectation'), [('\n   wqreq  \n', False), ('\n\t true   \t', True)])
def test_is_available(
    return_value: str, expectation: bool, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert is_available() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_is_available_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert not is_available()
    assert subprocess_check_output.call_args_list == snapshot


@pytest.mark.parametrize(('return_value', 'expectation'), [('\n   wqreq  \n', False), ('\n\t true   \t', True)])
def test_has_discrete_gpu(
    return_value: str, expectation: bool, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert has_discrete_gpu() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_has_discrete_gpu_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert not has_discrete_gpu()
    assert subprocess_check_output.call_args_list == snapshot


@pytest.mark.parametrize(
    ('return_value', 'expectation'), [('\n   1  \n', '1'), ('\n\t 2   \t', '2'), ('\n\t\n       \t    ', None)]
)
def test_get_discrete_gpu_index(
    return_value: str, expectation: str | None, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert get_discrete_gpu_index() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_get_discrete_gpu_index_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert get_discrete_gpu_index() is None
    assert subprocess_check_output.call_args_list == snapshot


@pytest.mark.parametrize(
    ('return_value', 'expectation'),
    [('\n   gpu 1  \n', 'gpu 1'), ('\n\t gpu 2.4   \t', 'gpu 2.4'), ('\n\t\n       \t    ', None)],
)
def test_get_discrete_gpu_name(
    return_value: str, expectation: str | None, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert get_discrete_gpu_name() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_get_discrete_gpu_name_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert get_discrete_gpu_name() is None
    assert subprocess_check_output.call_args_list == snapshot


@pytest.mark.parametrize(
    ('return_value', 'expectation'),
    [('\n   UUID1  \n', 'UUID1'), ('\n\t UUID2   \t', 'UUID2'), ('\n\t\n       \t    ', None)],
)
def test_get_discrete_gpu_uuid(
    return_value: str, expectation: str | None, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert get_discrete_gpu_uuid() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_get_discrete_gpu_uuid_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert get_discrete_gpu_uuid() is None
    assert subprocess_check_output.call_args_list == snapshot


@pytest.mark.parametrize(
    ('return_value', 'expectation'),
    [('\n   1.2.2  \n', '1.2.2'), ('\n\t 1.3.12   \t', '1.3.12'), ('\n\t\n       \t    ', '')],
)
def test_get_version(
    return_value: str, expectation: str, subprocess_check_output: Mock, snapshot: SnapshotAssertion
) -> None:
    subprocess_check_output.return_value = return_value
    assert get_version() == expectation
    assert subprocess_check_output.call_args_list == snapshot


def test_get_version_error(subprocess_check_output: Mock, snapshot: SnapshotAssertion) -> None:
    subprocess_check_output.side_effect = CalledProcessError(1, [])
    assert get_version() == ''
    assert subprocess_check_output.call_args_list == snapshot
