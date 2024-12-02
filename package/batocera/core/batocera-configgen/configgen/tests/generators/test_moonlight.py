from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.moonlight.moonlightGenerator import MoonlightGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


class TestMoonlightGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[MoonlightGenerator]:
        return MoonlightGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'moonlight'

    @pytest.fixture
    def emulator(self) -> str:
        return 'moonlight'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir('/usr/share/moonlight')
        fs.create_file(
            CONFIGS / 'moonlight' / 'gamelist.txt',
            contents="""rom;My Rom
rom-with-config;Another Rom;/path/to/moonlight.conf
""",
        )
        return fs

    def test_get_resolution_mode(self, generator: MoonlightGenerator) -> None:  # pyright: ignore
        assert generator.getResolutionMode({}) == 'default'

    def test_generate(
        self,
        generator: MoonlightGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/monlight/rom.moonlight',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'moonlight' / 'staging' / 'moonlight.conf').read_text() == snapshot(name='config')
        assert Path('/usr/share/moonlight/gamecontrollerdb.txt').read_text() == snapshot(name='controllerdb')

    def test_generate_rom_with_config_file(
        self,
        generator: MoonlightGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/monlight/rom-with-config.moonlight',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_rom_not_in_gamelist(
        self,
        generator: MoonlightGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/monlight/not-found.moonlight',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_user_config(
        self,
        generator: MoonlightGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'moonlight' / 'moonlight.conf',
            contents="""width = 640
height = 480
rotate = 90
foo = bar
""",
        )

        generator.generate(
            mock_system,
            '/userdata/roms/monlight/rom.moonlight',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'moonlight' / 'staging' / 'moonlight.conf').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'moonlight_codec': 'h264'},
            {'moonlight_resolution': '0'},
            {'moonlight_resolution': '1'},
            {'moonlight_resolution': '2'},
            {'moonlight_rotate': '90'},
            {'moonlight_framerate': '0'},
            {'moonlight_framerate': '1'},
            {'moonlight_framerate': '2'},
            {'moonlight_bitrate': '0'},
            {'moonlight_bitrate': '1'},
            {'moonlight_bitrate': '2'},
            {'moonlight_bitrate': '3'},
            {'moonlight_sops': 'True'},
            {'moonlight_sops': 'False'},
            {'moonlight_quitapp': 'True'},
            {'moonlight_quitapp': 'False'},
            {'moonlight_viewonly': 'True'},
            {'moonlight_viewonly': 'False'},
            {'moonlight_remote': 'yes'},
            {'moonlight_remote': 'no'},
            {'moonlight_surround': '7.1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: MoonlightGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/monlight/rom.moonlight',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'moonlight' / 'staging' / 'moonlight.conf').read_text() == snapshot
