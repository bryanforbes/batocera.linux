from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.solarus.solarusGenerator import SolarusGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestSolarusGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SolarusGenerator]:
        return SolarusGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'solarus'

    @pytest.fixture
    def emulator(self) -> str:
        return 'solarus'

    def test_generate(
        self,
        generator: SolarusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'solarus' / 'rom.solarus',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'joystick': 'normal'},
            {'joystick': 'joystick1'},
            {'joystick': 'joystick2'},
        ],
        ids=str,
    )
    def test_generate_joystick(
        self,
        generator: SolarusGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'solarus' / 'rom.solarus',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')

    def test_generate_keyboard(
        self,
        generator: SolarusGenerator,
        mock_system: Emulator,
        keyboard_controller: Controller,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'solarus' / 'rom.solarus',
            make_player_controller_list(keyboard_controller, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')

    def test_generate_no_controllers(
        self,
        generator: SolarusGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'solarus' / 'rom.solarus',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'solarus' / 'pads.ini').read_text() == snapshot(name='pads')
