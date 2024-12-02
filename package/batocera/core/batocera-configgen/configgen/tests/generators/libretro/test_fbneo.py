from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('fbneo')
@pytest.mark.fallback_system_name('fbneo')
class TestLibretroGeneratorFBNeo(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'fbneo-cpu-speed-adjust': '30%'},
            {'fbneo-frameskip': '1'},
        ],
        {
            'neogeo': [
                {
                    'fbneo-neogeo-mode-switch': [
                        'MVS Asia/Europe',
                        'MVS USA',
                        'MVS Japan',
                        'AES Asia',
                        'AES Japan',
                    ]
                },
                {'fbneo-memcard-mode': 'shared'},
            ]
        },
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs(
        [
            {},
            {'fbneo-lightgun-crosshair-emulation': ['always show', 'always hide']},
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
