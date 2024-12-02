from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.samcoupe.samcoupeGenerator import SamcoupeGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestSamcoupeGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert SamcoupeGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            SamcoupeGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/samcoupe/rom.dsk',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
