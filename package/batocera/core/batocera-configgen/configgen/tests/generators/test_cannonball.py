from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.cannonball.cannonballGenerator import CannonballGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestCannonballGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[CannonballGenerator]:
        return CannonballGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'cannonball'

    @pytest.fixture
    def emulator(self) -> str:
        return 'cannonball'

    def test_generate(
        self,
        generator: CannonballGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'cannonball' / 'rom.cannonball',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cannonball' / 'config.xml').read_text() == snapshot(name='config')
        assert (CONFIGS / 'cannonball' / 'gamecontrollerdb.txt').read_text() == snapshot(name='gamecontrollerdb')

    def test_generate_non_default_options(
        self,
        generator: CannonballGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        mock_system.config = SystemConfig({'showFPS': 'true', 'ratio': '1', 'highResolution': '1'})

        assert (
            generator.generate(
                mock_system,
                ROMS / 'cannonball' / 'rom.cannonball',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cannonball' / 'config.xml').read_text() == snapshot(name='config')
