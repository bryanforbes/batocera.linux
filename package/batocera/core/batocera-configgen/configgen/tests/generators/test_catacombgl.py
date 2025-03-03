from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.catacombgl.catacombglGenerator import CatacombGLGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestCatacombGLGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[CatacombGLGenerator]:
        return CatacombGLGenerator

    def test_get_in_game_ratio(self, generator: CatacombGLGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    @pytest.mark.parametrize(
        'rom_name',
        [
            'Abyss',
            'Abyss_SW13',
            'Armageddon',
            'Apocalypse',
            'Descent',
        ],
    )
    def test_generate(
        self,
        generator: CatacombGLGenerator,
        mocker: MockerFixture,
        rom_name: str,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.ANY,
                ROMS / 'catacomb' / f'Catacomb {rom_name}.game',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'CatacombGL' / 'CatacombGL.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: CatacombGLGenerator,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'CatacombGL' / 'CatacombGL.ini',
            contents="""
WindowedScreenWidth=640
WindowedScreenHeight=480
""",
        )
        generator.generate(
            mocker.ANY,
            ROMS / 'catacomb' / 'Catacomb Abyss.game',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'CatacombGL' / 'CatacombGL.ini').read_text() == snapshot
