from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.ruffle.ruffleGenerator import RuffleGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestRuffleGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert RuffleGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert RuffleGenerator().getMouseMode({}, '')

    def test_generate(
        self,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            RuffleGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/flash/rom.swf',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
