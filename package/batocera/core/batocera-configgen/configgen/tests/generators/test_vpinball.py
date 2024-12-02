from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.vpinball.vpinballGenerator import VPinballGenerator

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


class TestVPinballGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'vpinball'

    @pytest.fixture
    def emulator(self) -> str:
        return 'vpinball'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(
            '/usr/bin/vpinball/assets/Default_VPinballX.ini',
            contents='[Standalone]\nLaunchTable = \n[Player]\nSound3D = \n[TableOverride]Difficulty = \n',
        )
        return fs

    @pytest.fixture(autouse=True)
    def get_service_status(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.utils.batoceraServices.batoceraServices.getServiceStatus', return_value='stopped'
        )

    @pytest.fixture(autouse=True)
    def get_screens_infos(self, mocker: MockerFixture, request: pytest.FixtureRequest) -> Mock:
        param = getattr(request, 'param', None)
        return_value = (
            param
            if param is not None
            else [
                {
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                }
            ]
        )
        return mocker.patch(
            'configgen.utils.videoMode.getScreensInfos',
            return_value=return_value,
        )

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert VPinballGenerator().getHotkeysContext() == snapshot

    def test_get_in_game_ratio(self) -> None:
        assert VPinballGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            VPinballGenerator().generate(
                mock_system,
                '/userdata/roms/vpinball/rom/rom.vpx',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'vpinball' / 'VPinballX.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'vpinball' / 'VPinballX.ini', contents='[Foo]\nBar = 1')
        fs.create_file(CONFIGS / 'vpinball' / 'vpinball.log', contents='log file')

        VPinballGenerator().generate(
            mock_system,
            '/userdata/roms/vpinball/rom/rom.vpx',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vpinball' / 'VPinballX.ini').read_text() == snapshot
        assert not (CONFIGS / 'vpinball' / 'vpinball.log').exists()
        assert (CONFIGS / 'vpinball' / 'vpinball.log.1').exists()

    def test_generate_existing_duplicate(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'vpinball' / 'VPinballX.ini', contents='[Foo]\nBar = 1\nBar = 2')

        VPinballGenerator().generate(
            mock_system,
            '/userdata/roms/vpinball/rom/rom.vpx',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vpinball' / 'VPinballX.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'vpinball_folders': '0'},
            {'vpinball_balltrail': '0.5'},
            {'vpinball_nudgestrength': '0.04'},
            {'vpinball_maxframerate': '50'},
            {'vpinball_vsync': '1'},
            {'vpinball_presets': 'defaults'},
            {'vpinball_presets': 'lowend'},
            {'vpinball_presets': 'highend'},
            {'vpinball_presets': 'manual'},
            {'vpinball_customphysicalsetup': '1'},
            {'vpinball_customphysicalsetup': '1', 'vpinball_screenwidth': '20'},
            {'vpinball_customphysicalsetup': '1', 'vpinball_screenheight': '10'},
            {'vpinball_customphysicalsetup': '1', 'vpinball_screeninclination': '10'},
            {'vpinball_customphysicalsetup': '1', 'vpinball_screenplayery': '0'},
            {'vpinball_customphysicalsetup': '1', 'vpinball_screenplayerz': '30'},
            {'vpinball_altcolor': '0'},
            {'vpinball_musicvolume': '20'},
            {'vpinball_soundvolume': '20'},
            {'vpinball_altsound': '0'},
            {'vpinball_sounddevice': 'sound-device-1'},
            {'vpinball_sounddevicebg': 'sound-device-2'},
            {'vpinball_pad_add_credit': '1'},
            {'vpinball_inverseplayfieldandb2s': '0'},
            {'vpinball_inverseplayfieldandb2s': '1'},
            {'vpinball_playfield': 'manual'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        VPinballGenerator().generate(
            mock_system,
            '/userdata/roms/vpinball/rom/rom.vpx',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vpinball' / 'VPinballX.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'get_screens_infos',
        [
            None,
            [
                {
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                },
                {
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                },
            ],
            [
                {
                    'width': 1920,
                    'height': 1080,
                    'x': 0,
                    'y': 0,
                },
                {
                    'width': 1080,
                    'height': 1920,
                    'x': 0,
                    'y': 0,
                },
            ],
        ],
        ids=str,
        indirect=True,
    )
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'vpinball_b2s': 'disabled'},
            {'vpinball_b2s': 'topright_small'},
            {'vpinball_b2s': 'topright_medium'},
            {'vpinball_b2s': 'topright_large'},
            {'vpinball_b2s': 'topleft_small'},
            {'vpinball_b2s': 'topleft_medium'},
            {'vpinball_b2s': 'topleft_large'},
            {'vpinball_b2s': 'screen2'},
            {'vpinball_b2s': 'screen2', 'vpinball_flexdmd': 'screen2'},
            {'vpinball_b2s': 'screen2', 'vpinball_pinmame': 'screen2'},
            {'vpinball_b2s': 'screen3'},
            {'vpinball_b2s': 'manual'},
        ],
        ids=str,
    )
    def test_generate_backglass(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        VPinballGenerator().generate(
            mock_system,
            '/userdata/roms/vpinball/rom/rom.vpx',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vpinball' / 'VPinballX.ini').read_text() == snapshot
