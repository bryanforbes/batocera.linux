from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.exceptions import InvalidConfiguration
from configgen.generators.raze.razeGenerator import RazeGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestRazeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[RazeGenerator]:
        return RazeGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'raze'

    @pytest.fixture
    def emulator(self) -> str:
        return 'raze'

    def test_get_in_game_ratio(self, generator: RazeGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    @pytest.fixture(autouse=True)
    def architecture(self, mocker: MockerFixture, request: SubRequest) -> Mock:
        mock_uname = mocker.Mock()
        mock_uname.machine = getattr(request, 'param', 'x86_64')
        return mocker.patch('platform.uname', return_value=mock_uname)

    def test_generate(
        self,
        generator: RazeGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/raze/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/raze/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/raze/rom.raze',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'raze' / 'rom.raze',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'raze' / 'raze.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'raze' / 'raze.cfg').read_text() == snapshot(name='script')
        assert (SAVES / 'raze').is_dir()

    def test_generate_existing(
        self,
        generator: RazeGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'raze' / 'raze.ini',
            contents="""[GlobalSettings]
gl_es=false
vid_preferbackend=1
""",
        )
        fs.create_file('/userdata/roms/raze/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/raze/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/raze/rom.raze',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'raze' / 'rom.raze',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'raze' / 'raze.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'showFPS': 'true'},
            {'nologo': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: RazeGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/raze/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/raze/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/raze/rom.raze',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'raze' / 'rom.raze',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'raze' / 'raze.cfg').read_text() == snapshot(name='script')

    @pytest.mark.parametrize(
        'existing_config',
        [
            None,
            {'foo': 'bar'},
            {'gl_es': 'true'},
            {'gl_es': 'false', 'vid_preferbackend': '2'},
            {'vid_preferbackend': '1'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize(
        ('mock_system_config'),
        [
            {'raze_api': '0'},
            {'raze_api': '1'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize('architecture', ['x86_64', 'amd64', 'i686', 'i386', 'arm64'], indirect=True)
    def test_generate_raze_api(
        self,
        generator: RazeGenerator,
        existing_config: dict[str, str] | None,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/raze/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/raze/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/raze/rom.raze',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        if existing_config is not None:
            fs.create_file(
                CONFIGS / 'raze' / 'raze.ini',
                contents=f"""[GlobalSettings]
{'\n'.join([f'{key}={value}' for key, value in existing_config.items()])}
""",
            )

        generator.generate(
            mock_system,
            ROMS / 'raze' / 'rom.raze',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'raze' / 'raze.ini').read_text() == snapshot

    def test_generate_raises(
        self,
        generator: RazeGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(
            '/userdata/roms/raze/rom.raze',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        with pytest.raises(InvalidConfiguration, match=r'^2 error\(s\) found in /userdata/roms/raze/rom\.raze'):
            generator.generate(
                mock_system,
                ROMS / 'raze' / 'rom.raze',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
