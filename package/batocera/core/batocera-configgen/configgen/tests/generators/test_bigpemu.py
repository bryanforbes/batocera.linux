from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.bigpemu.bigpemuGenerator import BigPEmuGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestBigPEmuGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[BigPEmuGenerator]:
        return BigPEmuGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'jaguar'

    @pytest.fixture
    def emulator(self) -> str:
        return 'bigpemu'

    @pytest.fixture(autouse=True)
    def video_mode(self, mocker: MockerFixture, video_mode: Mock) -> Mock:
        mocker.patch('configgen.generators.bigpemu.bigpemuGenerator.videoMode', video_mode)
        return video_mode

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'bigpemu_ratio': '2'}, 4 / 3),
            ({'bigpemu_ratio': '8'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: BigPEmuGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: BigPEmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'jaguar' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: BigPEmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg', contents='existing config')

        generator.generate(
            mock_system,
            ROMS / 'jaguar' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'bigpemu_vsync': '0'},
            {'bigpemu_ratio': '8'},
            {'bigpemu_avp': '1'},
            {'bigpemu_avp_mp': '1'},
            {'bigpemu_brett_hull_hockey': '1'},
            {'bigpemu_checkered_flag': '1'},
            {'bigpemu_cybermorph': '1'},
            {'bigpemu_iron_soldier': '1'},
            {'bigpemu_mc3d_vr': '1'},
            {'bigpemu_t2k_rotary': '1'},
            {'bigpemu_wolf3d': '1'},
            {'bigpemu_doom': '1'},
            {'bigpemu_screenfilter': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: BigPEmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'jaguar' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg').read_text() == snapshot(name='config')

    def test_generate_controllers(
        self,
        generator: BigPEmuGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'jaguar' / 'rom.zip',
            make_player_controller_list(
                generic_xbox_pad,
                ps3_controller,
                generic_xbox_pad,
                ps3_controller,
                generic_xbox_pad,
                ps3_controller,
                generic_xbox_pad,
                ps3_controller,
                generic_xbox_pad,
            ),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg').read_text() == snapshot(name='config')

    def test_generate_controllers_missing_inputs(
        self,
        generator: BigPEmuGenerator,
        mock_system: Emulator,
        gpio_controller_1: Controller,
        gpio_controller_2: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'jaguar' / 'rom.zip',
            make_player_controller_list(
                gpio_controller_1,
                gpio_controller_2,
            ),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'bigpemu' / 'BigPEmuConfig.bigpcfg').read_text() == snapshot(name='config')
