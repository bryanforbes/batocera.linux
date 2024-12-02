from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.fba2x.fba2xGenerator import Fba2xGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestFba2xGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Fba2xGenerator]:
        return Fba2xGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'neogeo'

    @pytest.fixture
    def emulator(self) -> str:
        return 'fba2x'

    def test_generate(
        self,
        generator: Fba2xGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'neogeo' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: Fba2xGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'fba' / 'fba2x.cfg',
            contents="""[Graphics]
DisplaySmoothStretch = 1

[Joystick]
SDLID_1 = 1

[Foo]
Bar = 2
""",
        )
        generator.generate(
            mock_system,
            ROMS / 'neogeo' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'smooth': '0'},
            {'smooth': '1'},
            {'ratio': '4/3'},
            {'ratio': '16/9'},
            {'ratio': 'full'},
            {'shaders': 'foo'},
            {'shaders': 'scanlines'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Fba2xGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'neogeo' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot

    def test_generate_six_button_game(
        self,
        generator: Fba2xGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'neogeo' / 'sfa.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot

    def test_generate_controllers(
        self,
        generator: Fba2xGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        gpio_controller_1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'neogeo' / 'sfa.zip',
            make_player_controller_list(generic_xbox_pad, gpio_controller_1),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot
