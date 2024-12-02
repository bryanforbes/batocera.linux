from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.generators.x16emu.x16emuGenerator import X16emuGenerator
from tests.generators.conftest import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestX16emuGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'commanderx16'

    @pytest.fixture
    def emulator(self) -> str:
        return 'x16emu'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert X16emuGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'x16emu_ratio': '4:3'}, 4 / 3),
            ({'x16emu_ratio': '16:9'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert X16emuGenerator().getInGameRatio(mock_system_config, {'width': 0, 'height': 0}, '') == result

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            X16emuGenerator().generate(
                mock_system,
                '/userdata/roms/commanderx16/rom-name.bas',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'x16emu_scale': '3'},
            {'x16emu_quality': 'linear'},
            {'x16emu_ratio': '4:3'},
            {'x16emu_ratio': '16:9'},
        ],
        ids=str,
    )
    def test_generate_config(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            X16emuGenerator().generate(
                mock_system,
                '/userdata/roms/commanderx16/rom-name.bas',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['img', 'prg'])
    def test_generate_rom(
        self,
        extension: str,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            X16emuGenerator().generate(
                mock_system,
                f'/userdata/roms/commanderx16/rom-name.{extension}',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_autorun(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/commanderx16/rom-dir/autorun.cmd')

        assert (
            X16emuGenerator().generate(
                mock_system,
                '/userdata/roms/commanderx16/rom-dir/rom.bas',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            X16emuGenerator().generate(
                mock_system,
                '/userdata/roms/commanderx16/rom-dir/rom.bas',
                make_player_controller_dict(
                    generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad
                ),
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
