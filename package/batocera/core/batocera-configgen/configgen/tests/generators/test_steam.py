from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.steam.steamGenerator import SteamGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestSteamGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert SteamGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert SteamGenerator().getMouseMode({}, '')

    def test_generate(
        self,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            SteamGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/steam/Steam.steam',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_game_rom(
        self,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/steam/rom.steam', contents='\t\n GAMEID\t  \n')

        assert (
            SteamGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/steam/rom.steam',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
