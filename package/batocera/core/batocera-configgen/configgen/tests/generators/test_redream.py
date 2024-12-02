from __future__ import annotations

import shutil
import stat
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.redream.redreamGenerator import RedreamGenerator
from tests.generators.conftest import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


class TestRedreamGenerator:
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

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert RedreamGenerator().getHotkeysContext() == snapshot

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
    def test_get_in_game_ratio(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert RedreamGenerator().getInGameRatio(mock_system_config, {'width': 0, 'height': 0}, '') == result

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            RedreamGenerator().generate(
                mock_system,
                '/userdata/roms/dreamcast/rom.chd',
                one_player_controllers,
                {},
                {},
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
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(CONFIGS / 'redream')
        shutil.copyfile('/usr/bin/redream', CONFIGS / 'redream' / 'redream')

        RedreamGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert stat.filemode((CONFIGS / 'redream' / 'redream').stat().st_mode) == snapshot(name='filemode')

    def test_generate_existing_different(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'redream' / 'redream', contents='older redream bin')

        RedreamGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            one_player_controllers,
            {},
            {},
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
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        RedreamGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'redream' / 'redream.cfg').read_text() == snapshot

    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        nintendo_pro_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            RedreamGenerator().generate(
                mock_system,
                '/userdata/roms/dreamcast/rom.chd',
                make_player_controller_dict(
                    generic_xbox_pad, ps3_controller, nintendo_pro_controller, ps3_controller, generic_xbox_pad
                ),
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'redream' / 'redream.cfg').read_text() == snapshot(name='config')
