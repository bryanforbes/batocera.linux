from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest, parametrize_guns

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator
    from configgen.types import DeviceInfoDict


@pytest.mark.core('flycast')
@pytest.mark.fallback_system_name('dreamcast')
class TestLibretroGeneratorFlycast(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'reicast_synchronous_rendering': 'disabled'},
            {'reicast_internal_resolution': '800x600'},
            {'reicast_dsp': 'enabled'},
            {'reicast_mipmapping': 'enabled'},
            {'reicast_anisotropic_filtering': '2'},
            {'reicast_texupscale': '2'},
            {'reicast_frame_skipping': '1'},
            {'reicast_region': 'Usa'},
            {'reicast_language': 'English'},
            {'reicast_force_wince': 'enabled'},
            {'reicast_widescreen_cheats': 'enabled', 'ratio': '16/9', 'bezel': 'none'},
            {
                'reicast_widescreen_hack': 'enabled',
                'reicast_widescreen_cheats': 'disabled',
                'ratio': '16/9',
                'bezel': 'none',
            },
            {'controller1_dc': '2'},
            {'controller2_dc': '2'},
            {'controller3_dc': '2'},
            {'controller4_dc': '2'},
        ],
        {
            'atomiswave': [{'screen_rotation_atomiswave': 'horizontal'}],
            'naomi': [{'screen_rotation_naomi': 'horizontal'}],
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('mock_system_config', [{}, {'flycast_offscreen_reload': '1'}], ids=str)
    @parametrize_guns
    def test_generate_guns(
        self, mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
    ) -> None:
        return super().test_generate_guns(
            mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
        )

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs(
        [
            {'reicast_lightgun1_crosshair': ['disabled', 'Blue']},
            {'reicast_lightgun2_crosshair': ['disabled', 'Green']},
            {'reicast_lightgun3_crosshair': ['disabled', 'White']},
            {'reicast_lightgun4_crosshair': ['disabled', 'Red']},
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

    @pytest.mark.parametrize_core_configs([{'use_wheels': ['0', '1']}])
    @pytest.mark.parametrize('wheels', [{}, {'mock': {}}])
    def test_generate_wheels(
        self,
        generator: Generator,
        default_extension: str,
        mock_system: Emulator,
        wheels: DeviceInfoDict,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            wheels,
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)
