from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.generators.sh.shGenerator import ShGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestShGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert ShGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert ShGenerator().getMouseMode({}, '')

    def test_generate(
        self,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            ShGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/ports/rom.sh',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert Path('/tmp/gamecontrollerdb.txt').read_text() == snapshot(name='controllerdb')

    def test_generate_run_sh(
        self,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/ports/rom.sh/run.sh')

        assert (
            ShGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/ports/rom.sh',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
