from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.odcommander.odcommanderGenerator import OdcommanderGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestOdcommanderGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert OdcommanderGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = OdcommanderGenerator().generate(
            mocker.Mock(),
            '',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
