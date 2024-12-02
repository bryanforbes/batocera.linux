from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.shadps4.shadps4Generator import shadPS4Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures(
    'fs', 'vulkan_is_available', 'vulkan_get_version', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index'
)
class TestShadPS4Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[shadPS4Generator]:
        return shadPS4Generator

    @pytest.fixture(autouse=True)
    def vulkan_is_available(self, vulkan_is_available: Mock) -> Mock:
        vulkan_is_available.return_value = True
        return vulkan_is_available

    def test_get_in_game_ratio(self, generator: shadPS4Generator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: shadPS4Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'ps4' / 'ROMDIR' / 'rom.ps4',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'shadps4' / 'user' / 'config.toml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: shadPS4Generator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'shadps4' / 'user' / 'config.toml')

        generator.generate(
            mock_system,
            ROMS / 'ps4' / 'ROMDIR' / 'rom.ps4',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'shadps4' / 'user' / 'config.toml').read_text() == snapshot

    def test_generate_config_rom(
        self,
        generator: shadPS4Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('config'),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        ('vulkan_get_version', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index'),
        [
            pytest.param('1.3.2', False, None, id='vulkan available, incompatible version'),
            pytest.param('1.4.0', False, None, id='vulkan available, no discrete gpu'),
            pytest.param('1.4.0', True, None, id='vulkan available, unable to get gpu index'),
            pytest.param('1.4.0', True, '1', id='vulkan available'),
        ],
        indirect=True,
    )
    def test_generate_vulkan(
        self,
        generator: shadPS4Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'ps4' / 'ROMDIR' / 'rom.ps4',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'shadps4' / 'user' / 'config.toml').read_text() == snapshot

    def test_generate_vulkan_unavailable(
        self,
        generator: shadPS4Generator,
        mock_system: Emulator,
        vulkan_is_available: Mock,
        one_player_controllers: Controllers,
    ) -> None:
        vulkan_is_available.return_value = False

        with pytest.raises(SystemExit):
            generator.generate(
                mock_system,
                ROMS / 'ps4' / 'ROMDIR' / 'rom.ps4',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
