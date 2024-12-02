from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.config import SystemConfig
from configgen.generators.shadps4.shadps4Generator import shadPS4Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


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
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        generator: shadPS4Generator,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.ANY,
                '/userdata/roms/ps4/ROMDIR/rom.ps4',
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
        fs: FakeFilesystem,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'shadps4' / 'user' / 'config.toml')

        generator.generate(
            mocker.ANY,
            '/userdata/roms/ps4/ROMDIR/rom.ps4',
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
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.ANY,
                'config',
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
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mocker.ANY,
            '/userdata/roms/ps4/ROMDIR/rom.ps4',
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
        vulkan_is_available: Mock,
        mocker: MockerFixture,
        one_player_controllers: ControllerMapping,
    ) -> None:
        vulkan_is_available.return_value = False

        with pytest.raises(SystemExit):
            generator.generate(
                mocker.ANY,
                '/userdata/roms/ps4/ROMDIR/rom.ps4',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
