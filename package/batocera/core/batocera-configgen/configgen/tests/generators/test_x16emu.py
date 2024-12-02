from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.x16emu.x16emuGenerator import X16emuGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestX16emuGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[X16emuGenerator]:
        return X16emuGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'commanderx16'

    @pytest.fixture
    def emulator(self) -> str:
        return 'x16emu'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'x16emu_ratio': '4:3'}, 4 / 3),
            ({'x16emu_ratio': '16:9'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: X16emuGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: X16emuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'commanderx16' / 'rom-name.bas',
                one_player_controllers,
                {},
                [],
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
        self,
        generator: X16emuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'commanderx16' / 'rom-name.bas',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['img', 'prg'])
    def test_generate_rom(
        self,
        generator: X16emuGenerator,
        extension: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'commanderx16' / f'rom-name.{extension}',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_autorun(
        self,
        generator: X16emuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/commanderx16/rom-dir/autorun.cmd')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'commanderx16' / 'rom-dir' / 'rom.bas',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_controllers(
        self,
        generator: X16emuGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'commanderx16' / 'rom-dir' / 'rom.bas',
                make_player_controller_list(
                    generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad
                ),
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
