from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.taradino.taradinoGenerator import TaradinoGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestTaradinoGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert TaradinoGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = TaradinoGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/rott/rom.rott',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
