from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import pytest

from configgen.utils.hotkeygen import set_hotkeygen_context

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.fixture
def subprocess_call(mocker: MockerFixture) -> Mock:
    return mocker.patch('subprocess.call')


def test_set_hotkeygen_context(mocker: MockerFixture, subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    generator = mocker.Mock()
    generator.getHotkeysContext.return_value = {'name': 'test', 'keys': {'exit': ['KEY_LEFTALT', 'KEY_F4']}}

    with set_hotkeygen_context(generator):
        pass

    assert subprocess_call.call_args_list == snapshot


def test_set_hotkeygen_context_cleanup(
    mocker: MockerFixture, subprocess_call: Mock, snapshot: SnapshotAssertion
) -> None:
    generator = mocker.Mock()
    generator.getHotkeysContext.return_value = {'name': 'test', 'keys': {'exit': ['KEY_LEFTALT', 'KEY_F4']}}

    with suppress(Exception), set_hotkeygen_context(generator):
        raise Exception('test')

    assert subprocess_call.call_args_list == snapshot
