from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.generators.bigpemu.bigpemuGenerator import BigPEmuGenerator, bigPemuConfig
from tests.generators.conftest import make_player_controller

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestBigPEmuGenerator:
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

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert BigPEmuGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'bigpemu_ratio': '2'}, 4 / 3),
            ({'bigpemu_ratio': '8'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert BigPEmuGenerator().getInGameRatio(mock_system_config, {'width': 0, 'height': 0}, '') == result

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            BigPEmuGenerator().generate(
                mock_system,
                '/userdata/roms/jaguar/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert bigPemuConfig.read_text() == snapshot(name='config')

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
            {'bigpemu_screenfilter': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        BigPEmuGenerator().generate(
            mock_system,
            '/userdata/roms/jaguar/rom.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert bigPemuConfig.read_text() == snapshot(name='config')

    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad_p1: Controller,
        ps3_controller_p2: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        BigPEmuGenerator().generate(
            mock_system,
            '/userdata/roms/jaguar/rom.zip',
            {
                1: generic_xbox_pad_p1,
                2: ps3_controller_p2,
                3: make_player_controller(generic_xbox_pad_p1, 3),
                4: make_player_controller(ps3_controller_p2, 4),
                5: make_player_controller(generic_xbox_pad_p1, 5),
                6: make_player_controller(ps3_controller_p2, 6),
                7: make_player_controller(generic_xbox_pad_p1, 7),
                8: make_player_controller(ps3_controller_p2, 8),
                9: make_player_controller(generic_xbox_pad_p1, 9),
            },
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert bigPemuConfig.read_text() == snapshot(name='config')
