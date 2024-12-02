from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('mednafen_wswan')
@pytest.mark.fallback_system_name('wswan')
class TestLibretroGeneratorMenafenWswan(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs([{'wswan_rotate_display': 'landscape'}])
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize(
        ('system_name', 'rom_name'),
        [
            ('wswan', 'beat mania for WonderSwan (Japan)'),
            ('wswanc', 'Another Heaven - Memory of those Days (Japan)'),
        ],
    )
    def test_generate_mednafen_wswan_rotation(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        rom_name: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'{rom_name}.zip')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'{rom_name}.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)
