from __future__ import annotations

import filecmp
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, HOME
from configgen.generators.fpinball.fpinballGenerator import FpinballGenerator
from tests.conftest import get_os_environ
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('wine_install_wine_trick', 'wine_regedit')
class TestFpinballGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[FpinballGenerator]:
        return FpinballGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'fpinball'

    @pytest.fixture
    def emulator(self) -> str:
        return 'fpinball'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/fpinball/BAM/FPLoader.exe', contents='loader')

        return fs

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture) -> None:
        mocker.patch.dict('os.environ', values={'__VK_LAYER_NV_optimus': '1', 'FOO': 'BAR'}, clear=True)

    def test_generate(
        self,
        generator: FpinballGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        wine_install_wine_trick: Mock,
        wine_regedit: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/fpinball/rom.fpt',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        wine_install_wine_trick.assert_called_once_with(
            HOME / 'wine-bottles' / 'fpinball', 'wsh57', environment={'W_CACHE': BIOS}
        )
        assert filecmp.cmp(
            '/usr/fpinball/BAM/FPLoader.exe', HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe'
        )
        wine_regedit.assert_called_once_with(
            HOME / 'wine-bottles' / 'fpinball', CONFIGS / 'fpinball' / 'batocera.confg.reg'
        )
        assert (CONFIGS / 'fpinball' / 'batocera.confg.reg').read_text() == snapshot(name='regedit')

    def test_generate_config_rom(
        self,
        generator: FpinballGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                'config',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_existing_bottle(
        self,
        generator: FpinballGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_file(
            HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe', contents='existing bottle'
        )

        generator.generate(
            mock_system,
            '/userdata/roms/fpinball/rom.fpt',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (
            HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe'
        ).read_text() == 'existing bottle'

    def test_generate_old_bottle(
        self,
        generator: FpinballGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_file(HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe', contents='old bottle')
        fs.utime(str(HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe'), (0, 0))

        generator.generate(
            mock_system,
            '/userdata/roms/fpinball/rom.fpt',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (HOME / 'wine-bottles' / 'fpinball' / 'fpinball' / 'BAM' / 'FPLoader.exe').read_text() == 'loader'

    @pytest.mark.mock_system_config({'fpcontroller': 'True'})
    def test_generate_controllers(
        self,
        generator: FpinballGenerator,
        mock_system: Emulator,
        two_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/fpinball/rom.fpt',
            two_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fpinball' / 'batocera.confg.reg').read_text() == snapshot(name='regedit')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'ratio': '4/3'},
            {'ratio': '16/9'},
            {'ratio': '16/10'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: FpinballGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/fpinball/rom.fpt',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'fpinball' / 'batocera.confg.reg').read_text() == snapshot(name='regedit')

    def test_generate_nvidia(
        self,
        generator: FpinballGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        two_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/fpinball/rom.fpt',
                two_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert get_os_environ() == snapshot(name='environ')
