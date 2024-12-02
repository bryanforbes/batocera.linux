from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest, parametrize_guns
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('pcsx_rearmed')
class TestLibretroGeneratorPCSXRearmed(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'show_bios_bootlogo': 'enabled'},
            {'frameskip_pcsx': '1'},
            {'neon_enhancement': ['disabled', 'enabled', 'enabled_with_speedhack']},
            {'pcsx_rearmed_multitap': 'port 1 only'},
            {
                'game_fixes_pcsx': [
                    'disabled',
                    'Capcom_fighting',
                    'Chrono_Chross',
                    'Dark_Forces',
                    'Diablo_Music_Fix',
                    'Lunar',
                    'InuYasha_Sengoku',
                    'Pandemonium',
                    'Parasite_Eve',
                ]
            },
            {'controller1_pcsx': ['1', '261']},
            {'controller2_pcsx': ['1', '261']},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @parametrize_guns(metadata=[{'gun_type': 'justifier'}])
    def test_generate_guns(
        self, mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
    ) -> None:
        return super().test_generate_guns(
            mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
        )

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs(
        [
            {'pcsx_rearmed_crosshair1': ['disabled', 'green']},
            {'pcsx_rearmed_crosshair2': ['disabled', 'white']},
        ]
    )
    @pytest.mark.usefixtures('guns_need_crosses')
    def test_generate_crosses_config(
        self, generator: Generator, default_extension: str, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_core_config_matches(snapshot)

    @pytest.mark.mock_system_config({'use_wheels': '1'})
    @pytest.mark.parametrize(
        ('get_devices_information', 'metadata'),
        [
            ({}, {}),
            ({'/dev/input/event1': {'isWheel': False}}, {}),
            ({'/dev/input/event1': {'isWheel': True}}, {}),
            ({'/dev/input/event1': {'isWheel': True}}, {'wheel_type': 'other'}),
            ({'/dev/input/event1': {'isWheel': True}}, {'wheel_type': 'negcon'}),
        ],
        indirect=['get_devices_information'],
        ids=[
            'no wheels',
            'player 1 not wheel',
            'player 1 wheel',
            'player 1 wheel other type',
            'player 1 wheel negcon type',
        ],
    )
    def test_generate_wheels(
        self,
        generator: Generator,
        default_extension: str,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        metadata: dict[str, str],
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, generic_xbox_pad, generic_xbox_pad),
            metadata,
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)
