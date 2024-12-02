from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('dosbox_pure')
class TestLibretroGeneratorDosboxPure(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'pure_cpu_type': ['automatic', '386']},
            {'pure_cpu_core': ['automatic', 'dynamic']},
            {'pure_cycles': ['automatic', 'max']},
            {'pure_machine': 'vga'},
            {'pure_memory_size': '64'},
            {'pure_savestate': 'rewind'},
            {'pure_keyboard_layout': 'uk'},
            {'pure_auto_mapping': 'notify'},
            {'pure_joystick_analog_deadzone': '20'},
            {'pure_joystick_timed': 'false'},
            {'pure_sblaster_type': 'sbpro2'},
            {'pure_gravis': 'true'},
            {'pure_midi': 'zcsf.sf2'},
            {'controller1_dosbox_pure': ['1', '3']},
            {'controller2_dosbox_pure': ['1', '3']},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize(
        ('extension', 'batfile', 'rom_has_space'),
        [
            pytest.param('pc', 0, False, id='pc'),
            pytest.param('pc', 1, False, id='pc-rom_dir.bat'),
            pytest.param('pc', 1, True, id='pc-rom dir.bat'),
            pytest.param('pc', 2, False, id='pc-dosbox.bat'),
            pytest.param('dos', 0, False, id='dos'),
            pytest.param('dos', 1, False, id='dos-rom_dir.bat'),
            pytest.param('dos', 1, True, id='dos-rom dir.bat'),
            pytest.param('dos', 2, False, id='dos-dosbox.bat'),
            pytest.param('zip', 0, False, id='zip'),
            pytest.param('dosz', 0, False, id='dosz'),
            pytest.param('m3u', 0, False, id='m3u'),
            pytest.param('iso', 0, False, id='iso'),
            pytest.param('cue', 0, False, id='cue'),
        ],
    )
    def test_generate_rom_extension(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        extension: str,
        batfile: int,
        rom_has_space: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        rom_stem = 'rom dir' if rom_has_space else 'rom_dir'
        rom_path = (
            Path(f'/var/run/squashfs/{rom_stem}')
            if extension == 'squashfs'
            else (ROMS / 'dos' / f'{rom_stem}.{extension}')
        )

        if batfile == 1:
            fs.create_file(f'{rom_path}/{rom_stem}.bat')
        elif batfile == 2:
            fs.create_file(f'{rom_path}/dosbox.bat')

        assert (
            generator.generate(
                mock_system,
                rom_path,
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
