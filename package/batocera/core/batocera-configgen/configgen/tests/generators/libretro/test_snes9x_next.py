from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.mock_controllers import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('snes9x_next')
class TestLibretroGeneratorSnes9xNext(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'2010_reduce_sprite_flicker': 'disabled'},
            {'2010_reduce_slowdown': 'light'},
            {'2010_overclock_superfx': '12 MHz'},
            {'hires_blend': 'merge'},
            {'controller1_snes9x_next': '2'},
            {'controller2_snes9x_next': '260'},
            {'snes9x_2010_blargg_filter': 'monochrome'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'superscope_crosshair': ['disabled', 'enabled']}])
    @pytest.mark.usefixtures('guns_need_crosses')
    def test_generate_crosses_config(
        self, generator: Generator, default_extension: str, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'retroarch' / 'cores' / 'retroarch-core-options.cfg').read_text() == snapshot(
            name='corecustom'
        )

    @pytest.mark.parametrize_core_configs([{'lightgun_map': ['0', '1']}])
    def test_generate_controllers_config(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
            make_player_controller_dict(generic_xbox_pad, ps3_controller, keyboard_controller),
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='retroarchcustom')
