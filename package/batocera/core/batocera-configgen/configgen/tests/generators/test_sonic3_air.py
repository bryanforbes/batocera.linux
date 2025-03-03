from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.sonic3_air.sonic3_airGenerator import Sonic3AIRGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestSonic3AIRGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Sonic3AIRGenerator]:
        return Sonic3AIRGenerator

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

    def test_get_mouse_mode(self, generator: Sonic3AIRGenerator) -> None:  # pyright: ignore
        assert not generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: Sonic3AIRGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: Sonic3AIRGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'sonic3-air' / 'rom.s3air',
                one_player_controllers,
                {},
                [],
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
        generator: Sonic3AIRGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
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

        generator.generate(
            mock_system,
            ROMS / 'sonic3-air' / 'rom.s3air',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'Sonic3AIR' / 'config.json').read_text() == snapshot(name='config.json')
        assert (CONFIGS / 'Sonic3AIR' / 'settings.json').read_text() == snapshot(name='settings.json')
        assert (CONFIGS / 'Sonic3AIR' / 'oxygenproject.json').read_text() == 'existing oxygen json'
