from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

from configgen.utils.hotkeygen import get_hotkeygen_event, set_hotkeygen_context

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


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


def test_get_hotkeygen_event(evdev: Mock) -> None:
    evdev.list_devices.return_value = ['/dev/input/event1', '/dev/input/event8']

    assert get_hotkeygen_event() is None


def test_get_hotkeygen_event_found_device(mocker: MockerFixture, evdev: Mock) -> None:
    mock_input_device1 = mocker.Mock()
    mock_input_device1.name = 'event 1'
    mock_input_device8 = mocker.Mock()
    mock_input_device8.name = 'batocera hotkeys'

    evdev.InputDevice.side_effect = [mock_input_device1, mock_input_device8]
    evdev.list_devices.return_value = ['/dev/input/event1', '/dev/input/event8', '/dev/input/event13']

    assert get_hotkeygen_event() == '/dev/input/event8'
