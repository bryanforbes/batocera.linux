from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest, parametrize_guns
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('snes9x')
@pytest.mark.fallback_system_name('snes')
class TestLibretroGeneratorSnes9x(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'reduce_sprite_flicker': 'disabled'},
            {'reduce_slowdown': 'light'},
            {'overclock_superfx': '50%'},
            {'hires_blend': 'merge'},
            {'controller1_snes9x': '2'},
            {'controller2_snes9x': '260'},
            {'controller3_snes9x': '772'},
            {'snes9x_blargg_filter': 'monochrome'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @parametrize_guns(metadata=[{'gun_type': 'justifier'}, {'gun_type': 'macsrifle'}, {'gun_reversedbuttons': 'true'}])
    def test_generate_guns(
        self, mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
    ) -> None:
        return super().test_generate_guns(
            mocker, generator, fs, default_extension, mock_system, metadata, controllers, snapshot
        )

    @pytest.mark.parametrize('guns_need_crosses', [True, False], indirect=True)
    @pytest.mark.parametrize_core_configs([{}, {'superscope_crosshair': ['disabled', 'enabled']}])
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
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, ps3_controller, keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        ('system_name', 'files'),
        [
            ('snes-msu1', ['rom.sfc', 'README.txt', 'foo.sfc']),
            ('snes-msu1', ['rom.smc', 'README.txt', 'foo.smc']),
            ('satellaview', ['rom.sfc', 'README.txt', 'foo.sfc']),
            ('satellaview', ['rom.smc', 'README.txt', 'foo.smc']),
        ],
    )
    def test_generate_squashfs_rom(
        self,
        generator: Generator,
        files: list[str],
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        for file in files:
            fs.create_file(f'/var/run/squashfs/rom_name/{file}')

        assert (
            generator.generate(
                mock_system,
                Path('/var/run/squashfs/rom_name'),
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
