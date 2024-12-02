from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.easyrpg.easyrpgGenerator import EasyRPGGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestEasyRPGGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[EasyRPGGenerator]:
        return EasyRPGGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'easyrpg'

    @pytest.fixture
    def emulator(self) -> str:
        return 'easyrpg'

    def test_generate(
        self,
        generator: EasyRPGGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'easyrpg' / 'rom.easyrpg',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'easyrpg' / 'config.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [{'showFPS': 'true'}, {'testplay': '1'}, {'encoding': 'autodetect'}, {'encoding': '1252'}],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: EasyRPGGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'easyrpg' / 'rom.easyrpg',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_two_controllers(
        self,
        generator: EasyRPGGenerator,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'easyrpg' / 'rom.easyrpg',
            two_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'easyrpg' / 'config.ini').read_text() == snapshot(name='config')
