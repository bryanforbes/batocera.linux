from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from configgen.batoceraPaths import CONFIGS, SAVES
from tests.generators.conftest import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator
    from configgen.types import GunMapping


_FILES_DIR: Final = Path(__file__).parent / '__files__'


class TestSupermodelGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'model3'

    @pytest.fixture
    def emulator(self) -> str:
        return 'supermodel'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/share/supermodel/NVRAM/0.nv', contents='0')
        fs.create_file('/usr/share/supermodel/NVRAM/foo.txt')
        fs.create_file('/usr/share/supermodel/Assets/bar.txt', contents='assets bar')
        fs.create_file('/usr/share/supermodel/Games.xml', contents='games.xml')
        fs.add_real_file(
            _FILES_DIR / 'Supermodel.ini.template', target_path='/usr/share/supermodel/Supermodel.ini.template'
        )
        fs.add_real_file(
            _FILES_DIR / 'Supermodel-Driving.ini.template',
            target_path='/usr/share/supermodel/Supermodel-Driving.ini.template',
        )

        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        assert SupermodelGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'m3_wideScreen': '0'}, 4 / 3),
            ({'m3_wideScreen': '1'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(self, mock_system_config: dict[str, Any], result: bool) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        assert (
            SupermodelGenerator().getInGameRatio(
                mock_system_config, {'width': 1, 'height': 1}, '/userdata/roms/model3/daytona2.zip'
            )
            == result
        )

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        assert (
            SupermodelGenerator().generate(
                mock_system,
                '/userdata/roms/model3/daytona2.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'supermodel' / 'NVRAM' / '0.nv').read_text() == '0'
        assert not (SAVES / 'supermodel' / 'foo.txt').exists()
        assert (CONFIGS / 'supermodel' / 'Assets' / 'bar.txt').read_text() == 'assets bar'
        assert (CONFIGS / 'supermodel' / 'Games.xml').read_text() == 'games.xml'

    def test_generate_existing(
        self, fs: FakeFilesystem, mock_system: Emulator, one_player_controllers: ControllerMapping
    ) -> None:
        fs.create_file(SAVES / 'supermodel' / 'NVRAM' / '0.nv', contents='new 0')
        fs.create_file(CONFIGS / 'supermodel' / 'Assets' / 'bar.txt', contents='new assets bar')
        fs.create_file(CONFIGS / 'supermodel' / 'Games.xml', contents='new games.xml')

        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        SupermodelGenerator().generate(
            mock_system,
            '/userdata/roms/model3/daytona2.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'supermodel' / 'NVRAM' / '0.nv').read_text() == 'new 0'
        assert (CONFIGS / 'supermodel' / 'Assets' / 'bar.txt').read_text() == 'new assets bar'
        assert (CONFIGS / 'supermodel' / 'Games.xml').read_text() == 'new games.xml'

    def test_generate_existing_old(
        self, fs: FakeFilesystem, mock_system: Emulator, one_player_controllers: ControllerMapping
    ) -> None:
        fs.create_file(SAVES / 'supermodel' / 'NVRAM' / '0.nv', contents='new 0')
        fs.create_file(SAVES / 'supermodel' / 'NVRAM' / '0.nv.bak', contents='old 0 bak')
        fs.create_file(CONFIGS / 'supermodel' / 'Assets' / 'bar.txt', contents='new assets bar')
        fs.create_file(CONFIGS / 'supermodel' / 'Games.xml', contents='new games.xml')
        fs.utime(str(SAVES / 'supermodel' / 'NVRAM' / '0.nv'), (0, 0))
        fs.utime(str(CONFIGS / 'supermodel' / 'Assets' / 'bar.txt'), (0, 0))
        fs.utime(str(CONFIGS / 'supermodel' / 'Games.xml'), (0, 0))

        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        SupermodelGenerator().generate(
            mock_system,
            '/userdata/roms/model3/daytona2.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'supermodel' / 'NVRAM' / '0.nv').read_text() == '0'
        assert (SAVES / 'supermodel' / 'NVRAM' / '0.nv.bak').read_text() == 'new 0'
        assert not (SAVES / 'supermodel' / 'foo.txt').exists()
        assert (CONFIGS / 'supermodel' / 'Assets' / 'bar.txt').read_text() == 'assets bar'
        assert (CONFIGS / 'supermodel' / 'Games.xml').read_text() == 'games.xml'

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'engine3D': 'new3d'},
            {'m3_wideScreen': '1', 'bezel': 'none'},
            {'quadRendering': '1'},
            {'crosshairs': '2'},
            {'forceFeedback': '1'},
            {'ppcFreq': '80'},
            {'crt_colour': '1'},
            {'upscale_mode': '3'},
            {'joystickSensitivity': '80'},
        ],
        ids=str,
    )
    def test_generate_config(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        assert (
            SupermodelGenerator().generate(
                mock_system,
                '/userdata/roms/model3/daytona2.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'supermodel' / 'Supermodel.ini').read_text() == snapshot(name='ini')

    @pytest.mark.mock_system_config({'pedalSwap': '1'})
    def test_generate_config_driving(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        SupermodelGenerator().generate(
            mock_system,
            '/userdata/roms/model3/daytona2.zip',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'supermodel' / 'Supermodel.ini').read_text() == snapshot(name='ini')

    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        SupermodelGenerator().generate(
            mock_system,
            '/userdata/roms/model3/daytona2.zip',
            make_player_controller_dict(generic_xbox_pad, ps3_controller),
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'supermodel' / 'Supermodel.ini').read_text() == snapshot(name='ini')

    @pytest.mark.mock_system_config({'use_guns': '1'})
    @pytest.mark.parametrize('guns', [{}, {1: {}}, {1: {}, 2: {}}], ids=str)
    def test_generate_guns(
        self,
        mocker: MockerFixture,
        guns: GunMapping,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        mocker.patch('configgen.controllersConfig.gunsNeedCrosses', return_value=True)

        from configgen.generators.supermodel.supermodelGenerator import SupermodelGenerator

        SupermodelGenerator().generate(
            mock_system,
            '/userdata/roms/model3/daytona2.zip',
            make_player_controller_dict(generic_xbox_pad, ps3_controller),
            {},
            guns,
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'supermodel' / 'Supermodel.ini').read_text() == snapshot(name='ini')
