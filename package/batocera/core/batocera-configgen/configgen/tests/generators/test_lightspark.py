from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.lightspark.lightsparkGenerator import LightsparkGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestLightsparkGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert LightsparkGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert LightsparkGenerator().getMouseMode({}, '')

    def test_generate(
        self,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            LightsparkGenerator().generate(
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
