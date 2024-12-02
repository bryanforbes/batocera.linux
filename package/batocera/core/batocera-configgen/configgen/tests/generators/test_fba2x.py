from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.fba2x.fba2xGenerator import Fba2xGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestFba2xGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'neogeo'

    @pytest.fixture
    def emulator(self) -> str:
        return 'fba2x'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert Fba2xGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = Fba2xGenerator().generate(
            mock_system,
            '/userdata/roms/neogeo/rom.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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
        Fba2xGenerator().generate(
            mock_system,
            '/userdata/roms/neogeo/rom.zip',
            one_player_controllers,
            {},
            {},
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
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        Fba2xGenerator().generate(
            mock_system,
            '/userdata/roms/neogeo/rom.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot

    def test_generate_six_button_game(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        Fba2xGenerator().generate(
            mock_system,
            '/userdata/roms/neogeo/sfa.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot

    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad_p1: Controller,
        gpio_controller_1_p2: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        Fba2xGenerator().generate(
            mock_system,
            '/userdata/roms/neogeo/sfa.zip',
            {
                generic_xbox_pad_p1.player_number: generic_xbox_pad_p1,
                gpio_controller_1_p2.player_number: gpio_controller_1_p2,
            },
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fba' / 'fba2x.cfg').read_text() == snapshot
