from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import SAVES
from configgen.generators.thextech.thextechGenerator import TheXTechGenerator

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestTheXTechGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'thextech'

    @pytest.fixture
    def emulator(self) -> str:
        return 'thextech'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert TheXTechGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            TheXTechGenerator().generate(
                mock_system,
                '/userdata/roms/thextech/rom.rott',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'thextech').is_dir()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'rendering_mode': 'sw'},
            {'frameskip': '0'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            TheXTechGenerator().generate(
                mock_system,
                '/userdata/roms/thextech/rom.rott',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'thextech').is_dir()
