from __future__ import annotations

import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, HOME, ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.lexaloffle.lexaloffleGenerator import LexaloffleGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestLexaloffleGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[LexaloffleGenerator]:
        return LexaloffleGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'pico8'

    @pytest.fixture
    def emulator(self) -> str:
        return 'lexaloffle'

    @pytest.fixture
    def core(self) -> str:
        return 'pico8_official'

    def test_get_in_game_ratio(self, generator: LexaloffleGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 4 / 3

    def test_generate(
        self,
        generator: LexaloffleGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'pico-8' / 'pico8', st_mode=stat.S_IXUSR)

        assert (
            generator.generate(
                mock_system,
                ROMS / 'pico8' / 'rom.p8',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (HOME / '.lexaloffle' / 'pico-8' / 'sdl_controllers.txt').read_text() == snapshot(name='controllers')

    @pytest.mark.system_name('voxatron')
    def test_generate_voxatron(
        self,
        generator: LexaloffleGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            BIOS / 'voxatron' / 'vox',
            st_mode=stat.S_IXUSR,
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'voxatron' / 'rom.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (HOME / '.lexaloffle' / 'Voxatron' / 'sdl_controllers.txt').read_text() == snapshot(name='controllers')

    @pytest.mark.system_name('something_else')
    def test_generate_raises_system_name(
        self,
        generator: LexaloffleGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        with pytest.raises(
            BatoceraException,
            match=r'^The Lexaloffle generator has been called for an unknwon system: something_else.$',
        ):
            generator.generate(
                mock_system,
                ROMS / 'voxatron' / 'rom.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize('system_name', ['pico8', 'voxatron'])
    def test_generate_raises_no_bin_path(
        self,
        generator: LexaloffleGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        with pytest.raises(BatoceraException, match=r'^Lexaloffle official binary not found at '):
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize('system_name', ['pico8', 'voxatron'])
    def test_generate_raises_not_executable(
        self,
        generator: LexaloffleGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(BIOS / ('pico-8/pico8' if mock_system.name == 'pico8' else 'voxatron/vox'))

        with pytest.raises(BatoceraException, match=r'^\/userdata\/bios\/.* is not set as executable$'):
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize('rom_name', ['SpLoRe', 'CONSOle'])
    def test_generate_splore(
        self,
        generator: LexaloffleGenerator,
        rom_name: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'pico-8' / 'pico8', st_mode=stat.S_IXUSR)

        assert (
            generator.generate(
                mock_system,
                ROMS / 'pico8' / f'{rom_name}.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.mock_system_config({'showFPS': True})
    def test_generate_show_fps(
        self,
        generator: LexaloffleGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'pico-8' / 'pico8', st_mode=stat.S_IXUSR)

        assert (
            generator.generate(
                mock_system,
                ROMS / 'pico8' / 'rom.png',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_show_m3u(
        self,
        generator: LexaloffleGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'pico-8' / 'pico8', st_mode=stat.S_IXUSR)
        fs.create_file('/userdata/roms/pico8/rom_dir/rom.m3u', contents='one.png\ntwo.png')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'pico8' / 'rom_dir' / 'rom.m3u',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
