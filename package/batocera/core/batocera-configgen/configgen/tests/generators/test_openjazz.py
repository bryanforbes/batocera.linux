from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.openjazz.openjazzGenerator import OpenJazzGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestOpenJazzGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenJazzGenerator]:
        return OpenJazzGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'openjazz'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openjazz'

    @pytest.fixture
    def failing_open(self, mocker: MockerFixture) -> None:
        mocker.patch('pathlib.PosixPath.open', side_effect=Exception('Test exception'))

    def test_get_in_game_ratio(self, generator: OpenJazzGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: OpenJazzGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'openjazz' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    @pytest.mark.parametrize('video_options', [b'\x00', b'\x0a'])
    def test_generate_existing(
        self,
        generator: OpenJazzGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        nintendo_pro_controller: Controller,
        video_options: bytes,
        snapshot: SnapshotAssertion,
    ) -> None:
        # config file with 640x480 resolution and generic_xbox_pad
        fs.create_file(
            CONFIGS / 'openjazz' / 'openjazz.cfg',
            contents=(
                b'\x06\x80\x02\xe0\x01'
                + video_options
                + b'R\x00\x00@Q\x00\x00@P\x00\x00@O\x00\x00@ \x00\x00\x00 \x00\x00\x00\xe2\x00\x00@\xe4\x00\x00@\r\x00\x00\x00\x1b\x00\x00\x001\x00\x00\x002\x00\x00\x003\x00\x00\x004\x00\x00\x005\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\t\x00\x00\x00\x08\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x04\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00Jazz\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\x08'
            ),
        )

        generator.generate(
            mock_system,
            ROMS / 'openjazz' / 'rom.game',
            make_player_controller_list(nintendo_pro_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    def test_generate_invalid_config(
        self,
        generator: OpenJazzGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'openjazz' / 'openjazz.cfg', contents=b'')

        generator.generate(
            mock_system,
            ROMS / 'openjazz' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    @pytest.mark.usefixtures('failing_open')
    def test_generate_save_fails(
        self,
        generator: OpenJazzGenerator,
        mock_system: Emulator,
        nintendo_pro_controller: Controller,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'openjazz' / 'rom.game',
            make_player_controller_list(nintendo_pro_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not (CONFIGS / 'openjazz' / 'openjazz.cfg').exists()

    @pytest.mark.mock_system_config({'jazz_resolution': '640x480'})
    def test_generate_config(
        self,
        generator: OpenJazzGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'openjazz' / 'rom.game',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    def test_generate_controllers(
        self,
        generator: OpenJazzGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'openjazz' / 'rom.game',
                make_player_controller_list(generic_xbox_pad, ps3_controller),
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')
