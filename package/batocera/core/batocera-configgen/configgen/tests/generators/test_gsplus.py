from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.gsplus.gsplusGenerator import GSplusGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestGSplusGenerator(GeneratorBaseTest):
    @pytest.fixture
    def emulator(self) -> str:
        return 'gsplus'

    @pytest.fixture
    def generator_cls(self) -> type[GSplusGenerator]:
        return GSplusGenerator

    def test_generate(
        self,
        generator: GSplusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'apple2' / 'rom.po',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'gsplus_bios_filename': 'ROM.00'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: GSplusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'apple2' / 'rom.po',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('extension', ['dsk', 'do', 'nib'])
    def test_generate_roms(
        self,
        generator: GSplusGenerator,
        mock_system: Emulator,
        extension: str,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'apple2' / f'rom.{extension}',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')
