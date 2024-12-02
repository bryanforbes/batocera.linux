from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.generators.sonic_mania.sonic_maniaGenerator import SonicManiaGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


class TestSonicManiaGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'sonic-mania'

    @pytest.fixture
    def emulator(self) -> str:
        return 'sonic-mania'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/sonic-mania', contents='sonic mania bin')
        fs.create_dir('/userdata/roms/sonic-mania')
        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert SonicManiaGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert not SonicManiaGenerator().getMouseMode({}, '')

    def test_get_in_game_ratio(self) -> None:
        assert SonicManiaGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            SonicManiaGenerator().generate(
                mock_system,
                '/userdata/roms/sonic-mania/rom.sman',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/userdata/roms/sonic-mania/Settings.ini').read_text() == snapshot(name='settings')
        assert filecmp.cmp('/usr/bin/sonic-mania', '/userdata/roms/sonic-mania/sonic-mania')

    def test_generate_existing_bin(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_file('/userdata/roms/sonic-mania/sonic-mania', contents='existing sonic mania bin')

        SonicManiaGenerator().generate(
            mock_system,
            '/userdata/roms/sonic-mania/rom.sman',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path('/userdata/roms/sonic-mania/sonic-mania').read_text() == 'existing sonic mania bin'

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'smania_vsync': 'n'},
            {'smania_buffering': 'y'},
            {'smania_language': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        SonicManiaGenerator().generate(
            mock_system,
            '/userdata/roms/sonic-mania/rom.sman',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/roms/sonic-mania/Settings.ini').read_text() == snapshot
