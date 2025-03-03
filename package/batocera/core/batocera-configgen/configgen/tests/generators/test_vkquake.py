from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.vkquake.vkquakeGenerator import VKQuakeGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.types import Resolution


class TestVKQuakeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[VKQuakeGenerator]:
        return VKQuakeGenerator

    @pytest.mark.parametrize(
        ('resolution', 'result'),
        [
            ({'width': 640, 'height': 480}, 4 / 3),
            ({'width': 1920, 'height': 1080}, 16 / 9),
            ({'width': 1920, 'height': 1145}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: VKQuakeGenerator, resolution: Resolution, result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig({}), resolution, Path()) == result

    @pytest.mark.parametrize(
        'rom_name',
        [
            'Quake.quake',
            'Quake Mission Pack 1 - Scourge of Armagon.quake',
            'Quake Mission Pack 2 - Dissolution of Eternity.quake',
        ],
    )
    def test_generate(
        self,
        generator: VKQuakeGenerator,
        rom_name: str,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'quake' / rom_name,
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
