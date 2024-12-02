from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.play.playGenerator import PlayGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestPlayGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[PlayGenerator]:
        return PlayGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'namco2x6'

    @pytest.fixture
    def emulator(self) -> str:
        return 'play'

    @pytest.fixture(autouse=True)
    def evdev_input_device(self, mocker: MockerFixture, evdev: Mock) -> Mock:
        def input_device_side_effect(path: str) -> Mock:
            mock_instance = mocker.Mock()

            if path[-1] == '1':
                mock_instance.uniq = 'AA:BB:CC:DD:EE:01'
            else:
                mock_instance.uniq = ''
                mock_instance.info.vendor = 0x11
                mock_instance.info.product = 0x22
                mock_instance.info.version = 0x33

            return mock_instance

        mock_input_device = mocker.Mock(side_effect=input_device_side_effect)
        evdev.InputDevice = mock_input_device

        return mock_input_device

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'play_mode': '1'}, 4 / 3),
            ({'play_mode': '0'}, 16 / 9),
            ({'play_mode': '1', 'play_widescreen': 'false'}, 4 / 3),
            ({'play_mode': '0', 'play_widescreen': 'true'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: PlayGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(self, generator: PlayGenerator, mock_system: Emulator, snapshot: SnapshotAssertion) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'namco2x6' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'play' / 'Play Data Files' / 'config.xml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self, generator: PlayGenerator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            CONFIGS / 'play' / 'Play Data Files' / 'config.xml',
            contents='<Config><Preference Name="ps2.arcaderoms.directory" Type="path" Value="/userdata/roms/namco2x6" /><Preference Name="foo" Type="boolean" Value="false" /></Config>\n',
        )

        generator.generate(
            mock_system,
            ROMS / 'namco2x6' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'play' / 'Play Data Files' / 'config.xml').read_text() == snapshot

    def test_generate_rom_config(
        self, generator: PlayGenerator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('config'),
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_rom_chd(
        self, generator: PlayGenerator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'namco2x6' / 'rom.chd',
                [],
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
            {'play_vsync': 'false'},
            {'play_widescreen': 'true'},
            {'play_language': '0'},
            {'play_api': '1'},
            {'play_scale': '2'},
            {'play_mode': '0'},
            {'play_filter': 'true'},
        ],
        ids=str,
    )
    def test_generate_config(
        self, generator: PlayGenerator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'namco2x6' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'play' / 'Play Data Files' / 'config.xml').read_text() == snapshot

    def test_generate_controllers(
        self,
        generator: PlayGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'namco2x6' / 'rom.zip',
            make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'play' / 'Play Data Files' / 'inputprofiles' / 'default.xml').read_text() == snapshot
