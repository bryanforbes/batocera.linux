from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.cannonball.cannonballGenerator import CannonballGenerator

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestCannonballGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'cannonball'

    @pytest.fixture
    def emulator(self) -> str:
        return 'cannonball'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert CannonballGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            CannonballGenerator().generate(
                mock_system,
                '/userdata/roms/cannonball/rom.cannonball',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cannonball' / 'config.xml').read_text() == snapshot(name='config')
        assert (CONFIGS / 'cannonball' / 'gamecontrollerdb.txt').read_text() == snapshot(name='gamecontrollerdb')

    def test_generate_non_default_options(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        mock_system.config = {'showFPS': 'true', 'ratio': '1', 'highResolution': '1'}

        assert (
            CannonballGenerator().generate(
                mock_system,
                '/userdata/roms/cannonball/rom.cannonball',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cannonball' / 'config.xml').read_text() == snapshot(name='config')
