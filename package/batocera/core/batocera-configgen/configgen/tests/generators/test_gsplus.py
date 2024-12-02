from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.gsplus.gsplusGenerator import GSplusGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestGSplusGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[GSplusGenerator]:
        return GSplusGenerator

    def test_generate(
        self,
        generator: GSplusGenerator,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                '/userdata/roms/apple2/rom.po',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('extension', ['dsk', 'do', 'nib'])
    def test_generate_roms(
        self,
        generator: GSplusGenerator,
        extension: str,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mocker.Mock(),
            f'/userdata/roms/apple2/rom.{extension}',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')
