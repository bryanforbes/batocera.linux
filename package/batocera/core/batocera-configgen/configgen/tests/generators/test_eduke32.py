from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.exceptions import InvalidConfiguration
from configgen.generators.eduke32.eduke32Generator import EDuke32Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestEDuke32Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[EDuke32Generator]:
        return EDuke32Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'eduke32'

    @pytest.fixture
    def emulator(self) -> str:
        return 'eduke32'

    def test_generate(
        self,
        generator: EDuke32Generator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/eduke32/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/eduke32/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/eduke32/rom.eduke32',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'eduke32' / 'rom.eduke32',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'eduke32' / 'eduke32.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'eduke32' / 'autoexec.cfg').read_text() == snapshot(name='script')
        assert (SAVES / 'eduke32').is_dir()

    def test_generate_existing(
        self,
        generator: EDuke32Generator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'eduke32' / 'eduke32.cfg',
            contents="""[Screen Setup]
ScreenWidth = 640
ScreenHeight = 480
ScreenMode = 2
Foo = 3
""",
        )
        fs.create_file('/userdata/roms/eduke32/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/eduke32/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/eduke32/rom.eduke32',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'eduke32' / 'rom.eduke32',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'eduke32' / 'eduke32.cfg').read_text() == snapshot(name='config')

    @pytest.mark.core('fury')
    def test_generate_fury(
        self,
        generator: EDuke32Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'fury' / 'rom.grp',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'fury' / 'fury.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'fury' / 'autoexec.cfg').read_text() == snapshot(name='script')
        assert (SAVES / 'fury').is_dir()

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
        generator: EDuke32Generator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/eduke32/duke/DUKE3D.GRP')
        fs.create_file('/userdata/roms/eduke32/duke/duke3d_hrp.zip')
        fs.create_file(
            '/userdata/roms/eduke32/rom.eduke32',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'eduke32' / 'rom.eduke32',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'eduke32' / 'autoexec.cfg').read_text() == snapshot(name='script')

    def test_generate_raises(
        self,
        generator: EDuke32Generator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(
            '/userdata/roms/eduke32/rom.eduke32',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        with pytest.raises(
            InvalidConfiguration, match=r'^2 error\(s\) found in \/userdata\/roms\/eduke32\/rom\.eduke32'
        ):
            generator.generate(
                mock_system,
                ROMS / 'eduke32' / 'rom.eduke32',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
