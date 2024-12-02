from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, SAVES
from configgen.generators.ecwolf.ecwolfGenerator import ECWolfGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestECWolfGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert ECWolfGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf')

        command = ECWolfGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (SAVES / 'ecwolf').is_dir()
        assert (CONFIGS / 'ecwolf' / 'ecwolf.cfg').read_text() == snapshot(name='config')
        assert fs.cwd == '/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf'
