from __future__ import annotations

import shutil
import stat
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.redream.redreamGenerator import RedreamGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


class TestRedreamGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[RedreamGenerator]:
        return RedreamGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'dreamcast'

    @pytest.fixture
    def emulator(self) -> str:
        return 'redream'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/redream', contents='redream bin')
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'redreamRatio': '4:3'}, 4 / 3),
            ({'redreamRatio': '16:9'}, 16 / 9),
            ({'redreamRatio': 'stretch'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: RedreamGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: RedreamGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'dreamcast' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'redream' / 'redream').is_file()
        assert stat.filemode((CONFIGS / 'redream' / 'redream').stat().st_mode) == snapshot(name='filemode')
        assert (CONFIGS / 'redream' / 'redream.cfg').read_text() == snapshot(name='config')

    def test_generate_existing_same(
        self,
        generator: RedreamGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(CONFIGS / 'redream')
        shutil.copyfile('/usr/bin/redream', CONFIGS / 'redream' / 'redream')

        generator.generate(
            mock_system,
            ROMS / 'dreamcast' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert stat.filemode((CONFIGS / 'redream' / 'redream').stat().st_mode) == snapshot(name='filemode')

    def test_generate_existing_different(
        self,
        generator: RedreamGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'redream' / 'redream', contents='older redream bin')

        generator.generate(
            mock_system,
            ROMS / 'dreamcast' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert stat.filemode((CONFIGS / 'redream' / 'redream').stat().st_mode) == snapshot(name='filemode')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'redreamResolution': '3'},
            {'redreamRatio': '16:9'},
            {'redreamFrameSkip': '1'},
            {'redreamVsync': '1'},
            {'redreamRender': 'hle_perpixel'},
            {'redreamRegion': 'europe'},
            {'redreamLanguage': 'german'},
            {'redreamBroadcast': 'pal'},
            {'redreamCable': 'rgb'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: RedreamGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'dreamcast' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'redream' / 'redream.cfg').read_text() == snapshot

    def test_generate_controllers(
        self,
        generator: RedreamGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        nintendo_pro_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'dreamcast' / 'rom.chd',
                make_player_controller_list(
                    generic_xbox_pad, ps3_controller, nintendo_pro_controller, ps3_controller, generic_xbox_pad
                ),
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'redream' / 'redream.cfg').read_text() == snapshot(name='config')
