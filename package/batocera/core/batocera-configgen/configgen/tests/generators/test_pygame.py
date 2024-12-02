from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.generators.pygame.pygameGenerator import PygameGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestPygameGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert PygameGenerator().getHotkeysContext() == snapshot

    def test_get_in_game_ratio(self) -> None:
        assert PygameGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_execution_dir(self) -> None:
        assert (
            PygameGenerator().executionDirectory({}, '/userdata/roms/pygame/foo/bar/rom.pygame')
            == '/userdata/roms/pygame/foo/bar'
        )

    def test_generate(
        self,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = PygameGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/pygame/rom.pygame',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
