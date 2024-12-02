from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator
    from configgen.types import DeviceInfoDict


@pytest.mark.core('beetle-saturn')
class TestLibretroGeneratorBeetleSaturn(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'controller1_saturn': '5'},
            {'controller2_saturn': '5'},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs(
        [
            {},
            {'beetle-saturn_crosshair': ['Dot', 'Cross', 'Off']},
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
