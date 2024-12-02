from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.easyrpg.easyrpgGenerator import EasyRPGGenerator

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestEasyRPGGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'easyrpg'

    @pytest.fixture
    def emulator(self) -> str:
        return 'easyrpg'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert EasyRPGGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = EasyRPGGenerator().generate(
            mock_system,
            '/userdata/roms/easyrpg/rom.easyrpg',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'easyrpg' / 'config.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [{'showFPS': 'true'}, {'testplay': '1'}, {'encoding': 'autodetect'}, {'encoding': '1252'}],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = EasyRPGGenerator().generate(
            mock_system,
            '/userdata/roms/easyrpg/rom.easyrpg',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot

    def test_generate_two_controllers(
        self,
        mock_system: Emulator,
        two_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        EasyRPGGenerator().generate(
            mock_system,
            '/userdata/roms/easyrpg/rom.easyrpg',
            two_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'easyrpg' / 'config.ini').read_text() == snapshot(name='config')
