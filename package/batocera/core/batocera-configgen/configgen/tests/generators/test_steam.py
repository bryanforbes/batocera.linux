from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.steam.steamGenerator import SteamGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestSteamGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SteamGenerator]:
        return SteamGenerator

    def test_get_mouse_mode(self, generator: SteamGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_generate(
        self,
        generator: SteamGenerator,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'steam' / 'Steam.steam',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_game_rom(
        self,
        generator: SteamGenerator,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/steam/rom.steam', contents='\t\n GAMEID\t  \n')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'steam' / 'rom.steam',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
