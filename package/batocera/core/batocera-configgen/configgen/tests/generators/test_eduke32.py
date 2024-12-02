from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, SAVES
from configgen.generators.eduke32.eduke32Generator import EDuke32Generator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestEDuke32Generator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'eduke32'

    @pytest.fixture
    def emulator(self) -> str:
        return 'eduke32'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert EDuke32Generator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
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

        command = EDuke32Generator().generate(
            mock_system,
            '/userdata/roms/eduke32/rom.eduke32',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'eduke32' / 'eduke32.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'eduke32' / 'autoexec.cfg').read_text() == snapshot(name='script')
        assert (SAVES / 'eduke32').is_dir()

    def test_generate_existing(
        self,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
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

        EDuke32Generator().generate(
            mock_system,
            '/userdata/roms/eduke32/rom.eduke32',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'eduke32' / 'eduke32.cfg').read_text() == snapshot(name='config')

    @pytest.mark.core('fury')
    def test_generate_fury(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = EDuke32Generator().generate(
            mock_system,
            '/userdata/roms/fury/rom.grp',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
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
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
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

        command = EDuke32Generator().generate(
            mock_system,
            '/userdata/roms/eduke32/rom.eduke32',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'eduke32' / 'autoexec.cfg').read_text() == snapshot(name='script')

    def test_generate_raises(
        self,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/userdata/roms/eduke32/rom.eduke32',
            contents="""FILE = /duke/DUKE3D.GRP
FILE+ = /duke/duke3d_hrp.zip
""",
        )

        generator = EDuke32Generator()

        with pytest.raises(Exception, match=r'^2 error\(s\) found in /userdata/roms/eduke32/rom\.eduke32'):
            generator.generate(
                mock_system,
                '/userdata/roms/eduke32/rom.eduke32',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
