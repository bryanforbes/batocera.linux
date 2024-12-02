from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.wine.wineGenerator import WineGenerator
from tests.conftest import get_os_environ
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestWineGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[WineGenerator]:
        return WineGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'windows'

    @pytest.fixture
    def emulator(self) -> str:
        return 'wine'

    @pytest.fixture
    def core(self) -> str:
        return 'wine-tkg'

    @pytest.fixture(autouse=True)
    def subprocess_check_output(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('subprocess.check_output', return_value='de_DE')

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture) -> None:
        mocker.patch.dict('os.environ', values={'__VK_LAYER_NV_optimus': '1', 'FOO': 'BAR'}, clear=True)

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, False), ({'force_mouse': '1'}, True), ({'force_mouse': '0'}, False)],
        ids=str,
    )
    def test_get_mouse_mode(  # pyright: ignore
        self, generator: WineGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getMouseMode(SystemConfig(mock_system_config), Path()) == result

    def test_generate(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('windows_installers')
    def test_generate_windows_installers(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows_installers' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_no_language(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        subprocess_check_output: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        subprocess_check_output.return_value = '   '

        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_language_raises(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        subprocess_check_output: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        subprocess_check_output.side_effect = CalledProcessError(-1, [])

        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('mock_system_config', [{'sdl_config': 'true'}, {'sdl_config': 'false'}], ids=str)
    def test_generate_config(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_nvidia(
        self,
        generator: WineGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'windows' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert get_os_environ() == snapshot(name='environ')

    @pytest.mark.system_name('foo')
    def test_generate_raises(
        self,
        generator: WineGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        with pytest.raises(BatoceraException, match='Invalid system: foo'):
            generator.generate(
                mock_system,
                ROMS / 'windows_installers' / 'rom.wine',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
