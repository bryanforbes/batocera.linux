from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, SAVES
from configgen.generators.sonic3_air.sonic3_airGenerator import Sonic3AIRGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


class TestSonic3AIRGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'sonic3-air'

    @pytest.fixture
    def emulator(self) -> str:
        return 'sonic3-air'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(
            '/usr/bin/sonic3-air/config.json',
            contents="""{
\t// Paths
\t"ScriptsDir":     "scripts",
\t"MainScriptName": "main.lemon",
\t"SaveStatesDir":  "saves/states",
\t// Video
\t"WindowSize": "1200 x 740",
\t"GameScreen": "400 x 224",\t\t// Can be changed with numpad multiply/divide
\t"Filtering": "0"\t\t\t\t// Can be toggled with Alt + F
}""",
        )
        fs.create_file('/usr/bin/sonic3-air/oxygenproject.json', contents='oxygen json')
        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert Sonic3AIRGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert not Sonic3AIRGenerator().getMouseMode({}, '')

    def test_get_in_game_ratio(self) -> None:
        assert Sonic3AIRGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            Sonic3AIRGenerator().generate(
                mock_system,
                '/userdata/roms/sonic3-air/rom.s3air',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'sonic3-air').is_dir()
        assert (CONFIGS / 'Sonic3AIR' / 'config.json').read_text() == snapshot(name='config.json')
        assert (CONFIGS / 'Sonic3AIR' / 'settings.json').read_text() == snapshot(name='settings.json')
        assert (CONFIGS / 'Sonic3AIR' / 'oxygenproject.json').read_text() == 'oxygen json'

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'Sonic3AIR' / 'config.json',
            contents="""{
\t// Existing Paths
\t"ScriptsDir":     "scripts",
\t"MainScriptName": "foo.lemon",
\t"SaveStatesDir":  "/userdata/saves/sonic3-air",
\t// Existing Video
\t"WindowSize": "640 x 480",
\t"GameScreen": "400 x 224",\t\t// Can be changed with numpad multiply/divide
\t"Filtering": "1"\t\t\t\t// Can be toggled with Alt + F
}""",
        )
        fs.create_file(CONFIGS / 'Sonic3AIR' / 'oxygenproject.json', contents='existing oxygen json')
        fs.create_file(CONFIGS / 'Sonic3AIR' / 'settings.json', contents='{"Fullscreen": 0}')

        Sonic3AIRGenerator().generate(
            mock_system,
            '/userdata/roms/sonic3-air/rom.s3air',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'Sonic3AIR' / 'config.json').read_text() == snapshot(name='config.json')
        assert (CONFIGS / 'Sonic3AIR' / 'settings.json').read_text() == snapshot(name='settings.json')
        assert (CONFIGS / 'Sonic3AIR' / 'oxygenproject.json').read_text() == 'existing oxygen json'
