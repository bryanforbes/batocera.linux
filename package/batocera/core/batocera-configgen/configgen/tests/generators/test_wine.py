from __future__ import annotations

import os
from subprocess import CalledProcessError
from typing import TYPE_CHECKING, Any

import pytest

from configgen.generators.wine.wineGenerator import WineGenerator

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestWineGenerator:
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

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert WineGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, True), ({'force_mouse': '1'}, True), ({'force_mouse': '0'}, False)],
        ids=str,
    )
    def test_get_mouse_mode(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert WineGenerator().getMouseMode(mock_system_config, '') == result

    def test_generate(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('windows_installers')
    def test_generate_windows_installers(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows_installers/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_no_language(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        subprocess_check_output: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        subprocess_check_output.return_value = '   '

        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_language_raises(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        subprocess_check_output: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        subprocess_check_output.side_effect = CalledProcessError(-1, [])

        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('mock_system_config', [{'sdl_config': 'true'}, {'sdl_config': 'false'}], ids=str)
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_nvidia(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            WineGenerator().generate(
                mock_system,
                '/userdata/roms/windows/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert {key: value for key, value in os.environ.items() if key != 'PYTEST_CURRENT_TEST'} == snapshot(
            name='environ'
        )

    @pytest.mark.system_name('foo')
    def test_generate_raises(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        generator = WineGenerator()
        with pytest.raises(Exception, match='invalid system foo'):
            generator.generate(
                mock_system,
                '/userdata/roms/windows_installers/rom.wine',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
