from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('picodrive')
@pytest.mark.fallback_system_name('megadrive')
class TestLibretroGeneratorPicodrive(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'picodrive_sprlim': ['enabled', 'disabled']},
            {'picodrive_cropoverscan': ['enabled', 'disabled']},
            {'picodrive_controller1': '3 button pad'},
            {'picodrive_controller2': '3 button pad'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize_core_configs(
        [
            {'pd_controller1_mapping': ['retropad', 'megadrive']},
            {'pd_controller2_mapping': ['retropad', 'megadrive']},
            {'pd_controller3_mapping': ['retropad', 'megadrive']},
            {'pd_controller4_mapping': ['retropad', 'megadrive']},
        ]
    )
    def test_generate_controllers_config(
        self,
        generator: Generator,
        default_extension: str,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        ('name', 'guid'),
        [
            (None, None),
            ('8BitDo M30 gamepad', '05000000c82d00005106000000010000'),
            ('8Bitdo  8BitDo M30 gamepad', '03000000c82d00000650000011010000'),
            ('8BitDo M30 gamepad', '050000005e0400008e02000030110000'),
            ('8Bitdo  8BitDo M30 Modkit', '03000000c82d00000150000011010000'),
            ('8BitDo M30 Modkit', '05000000c82d00000151000000010000'),
            ('Retro Bit Bluetooth Controller', '0500000049190000020400001b010000'),
        ],
    )
    def test_generate_controllers_remap(
        self,
        generator: Generator,
        default_extension: str,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        name: str | None,
        guid: str | None,
        snapshot: SnapshotAssertion,
    ) -> None:
        controllers = make_player_controller_list(generic_xbox_pad)

        if name is not None:
            controllers[0].name = name
        if guid is not None:
            controllers[0].guid = guid

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)
