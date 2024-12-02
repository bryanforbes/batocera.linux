from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.abuse.abuseGenerator import AbuseGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestAbuseGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert AbuseGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self, one_player_controllers: ControllerMapping, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        command = AbuseGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/abuse/abuse.game',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
