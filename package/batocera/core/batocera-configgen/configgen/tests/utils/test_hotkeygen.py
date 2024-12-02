from __future__ import annotations

from contextlib import suppress
from typing import TYPE_CHECKING

import pytest

from configgen.utils.hotkeygen import get_hotkeygen_event, set_hotkeygen_context

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


@pytest.fixture
def emulator() -> str:
    return 'unset'


def test_set_hotkeygen_context(
    mocker: MockerFixture, mock_system: Emulator, subprocess_call: Mock, snapshot: SnapshotAssertion
) -> None:
    generator = mocker.Mock()
    generator.getHotkeysContext.return_value = {
        'name': 'test',
        'keys': {'exit': ['KEY_LEFTALT', 'KEY_F4'], 'menu': 'KEY_MENU'},
    }

    with set_hotkeygen_context(generator, mock_system):
        pass

    assert subprocess_call.call_args_list == snapshot


@pytest.mark.parametrize(
    ('mock_system_config', 'keys'),
    [
        ({'exithotkeyonly': '1'}, {'exit': 'KEY_EXIT', 'menu': 'KEY_MENU'}),
        ({'exithotkeyonly': '1'}, {'menu': 'KEY_MENU'}),
        ({'uimode': 'Full'}, {'exit': 'KEY_EXIT', 'menu': 'KEY_MENU'}),
        ({'uimode': 'Kiosk'}, {'exit': 'KEY_EXIT', 'menu': 'KEY_MENU'}),
        ({'uimode': 'Kiosk'}, {'exit': 'KEY_EXIT', 'b': 'KEY_B'}),
    ],
    ids=str,
)
def test_set_hotkeygen_context_config(
    mocker: MockerFixture,
    mock_system: Emulator,
    keys: dict[str, str],
    subprocess_call: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    generator = mocker.Mock()
    generator.getHotkeysContext.return_value = {
        'name': 'test',
        'keys': keys,
    }

    with set_hotkeygen_context(generator, mock_system):
        pass

    assert subprocess_call.call_args_list == snapshot


def test_set_hotkeygen_context_cleanup(
    mocker: MockerFixture, mock_system: Emulator, subprocess_call: Mock, snapshot: SnapshotAssertion
) -> None:
    generator = mocker.Mock()
    generator.getHotkeysContext.return_value = {'name': 'test', 'keys': {'exit': ['KEY_LEFTALT', 'KEY_F4']}}

    with suppress(Exception), set_hotkeygen_context(generator, mock_system):
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
