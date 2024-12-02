from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.generators.jazz2_native.jazz2_nativeGenerator import Jazz2_NativeGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestJazz2_NativeGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert Jazz2_NativeGenerator().getHotkeysContext() == snapshot

    def test_get_in_game_ratio(self) -> None:
        assert Jazz2_NativeGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/usr/share/jazz2')

        command = Jazz2_NativeGenerator().generate(
            mocker.Mock(),
            '',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert Path('/usr/share/jazz2/gamecontrollerdb.txt').read_text() == snapshot(name='controllerdb')
