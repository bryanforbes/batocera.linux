from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.sonic_mania.sonic_maniaGenerator import SonicManiaGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestSonicManiaGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SonicManiaGenerator]:
        return SonicManiaGenerator

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

    def test_get_mouse_mode(self, generator: SonicManiaGenerator) -> None:  # pyright: ignore
        assert not generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: SonicManiaGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: SonicManiaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'sonic-mania' / 'rom.sman',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/userdata/roms/sonic-mania/Settings.ini').read_text() == snapshot(name='settings')
        assert filecmp.cmp('/usr/bin/sonic-mania', '/userdata/roms/sonic-mania/sonic-mania')

    def test_generate_existing_bin(
        self,
        generator: SonicManiaGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file('/userdata/roms/sonic-mania/sonic-mania', contents='existing sonic mania bin')

        generator.generate(
            mock_system,
            ROMS / 'sonic-mania' / 'rom.sman',
            one_player_controllers,
            {},
            [],
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
        generator: SonicManiaGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'sonic-mania' / 'rom.sman',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/roms/sonic-mania/Settings.ini').read_text() == snapshot
