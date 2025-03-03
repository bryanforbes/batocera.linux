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


@pytest.mark.core('scummvm')
class TestLibretroGeneratorScummVM(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'scummvm_analog_deadzone': '5'},
            {'scummvm_gamepad_cursor_speed': '2.0'},
            {'scummvm_speed_hack': 'disabled'},
        ]
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    def test_generate_file_with_contents(
        self, generator: Generator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file('/userdata/roms/scummvm/game.scummvm', contents='monkey\n')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'scummvm' / 'game.scummvm',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
