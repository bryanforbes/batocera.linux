from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.solarus.solarusGenerator import SolarusGenerator
from tests.generators.conftest import make_player_controller_dict

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestSolarusGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'solarus'

    @pytest.fixture
    def emulator(self) -> str:
        return 'solarus'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert SolarusGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            SolarusGenerator().generate(
                mock_system,
                '/userdata/roms/solarus/rom.solarus',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'joystick': 'normal'},
            {'joystick': 'joystick1'},
            {'joystick': 'joystick2'},
        ],
        ids=str,
    )
    def test_generate_joystick(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        SolarusGenerator().generate(
            mock_system,
            '/userdata/roms/solarus/rom.solarus',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')

    def test_generate_keyboard(
        self,
        mock_system: Emulator,
        keyboard_controller: Controller,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        SolarusGenerator().generate(
            mock_system,
            '/userdata/roms/solarus/rom.solarus',
            make_player_controller_dict(keyboard_controller, generic_xbox_pad),
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')
