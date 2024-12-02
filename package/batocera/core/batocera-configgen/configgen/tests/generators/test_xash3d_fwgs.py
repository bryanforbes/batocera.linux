from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.generators.xash3d_fwgs.xash3dFwgsGenerator import Xash3dFwgsGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestXash3dFwgsGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Xash3dFwgsGenerator]:
        return Xash3dFwgsGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'xash3d_fwgs'

    @pytest.fixture
    def emulator(self) -> str:
        return 'xash3d_fwgs'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem, mocker: MockerFixture) -> FakeFilesystem:
        fs.create_file('/usr/lib/xash3d/hlsdk/hl/dlls/hl_amd64.so')
        fs.create_file('/usr/lib/xash3d/hlsdk/hl/cl_dlls/client_amd64.so')
        fs.create_file('/usr/lib/xash3d/hlsdk/opfor/dlls/opfor_amd64.so')
        fs.create_file('/usr/lib/xash3d/hlsdk/opfor/cl_dlls/client_amd64.so')
        fs.create_file('/usr/lib/xash3d/hlsdk/dmc/dlls/dmc_amd64.so')
        fs.create_file('/usr/lib/xash3d/hlsdk/dmc/cl_dlls/client_amd64.so')

        gamepad_target_path = f'/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/site-packages/configgen/generators/xash3d_fwgs/gamepad.cfg'

        fs.add_real_file(
            Path(__file__).parents[2] / 'configgen' / 'generators' / 'xash3d_fwgs' / 'gamepad.cfg',
            target_path=gamepad_target_path,
        )
        # We have to patch __file__ because it is used to get the default gamepad.cfg
        mocker.patch(
            'configgen.generators.xash3d_fwgs.xash3dFwgsGenerator.__file__',
            gamepad_target_path,
        )

        return fs

    def test_generate(
        self,
        generator: Xash3dFwgsGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'xash3d_fwgs' / 'rom')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xash3d_fwgs' / 'rom.game',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg').read_text() == snapshot(name='gamepad')
        assert (CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == snapshot(name='custom config')
        assert Path(ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').resolve() == Path(
            CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg'
        )
        assert (SAVES / 'xash3d_fwgs' / 'rom').is_dir()
        assert Path(ROMS / 'xash3d_fwgs' / 'rom' / 'save').resolve() == Path(SAVES / 'xash3d_fwgs' / 'rom')

    def test_generate_liblist(
        self,
        generator: Xash3dFwgsGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'xash3d_fwgs' / 'rom' / 'liblist.gam',
            contents=r"""some stuff
some other stuff
gamedll "dlls\opfor.dll"
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xash3d_fwgs' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg').read_text() == snapshot(name='gamepad')
        assert (CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == snapshot(name='custom config')
        assert Path(ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').resolve() == Path(
            CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg'
        )

    def test_generate_liblist_no_match(
        self,
        generator: Xash3dFwgsGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'xash3d_fwgs' / 'rom' / 'liblist.gam',
            contents=r"""some stuff
some other stuff
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xash3d_fwgs' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg').read_text() == snapshot(name='gamepad')
        assert (CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == snapshot(name='custom config')
        assert Path(ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').resolve() == Path(
            CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg'
        )

    def test_generate_liblist_not_found(
        self,
        generator: Xash3dFwgsGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'xash3d_fwgs' / 'rom' / 'liblist.gam',
            contents=r"""some stuff
some other stuff
gamedll "dlls\foo.dll"
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xash3d_fwgs' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg').read_text() == snapshot(name='config')
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg').read_text() == snapshot(name='gamepad')
        assert (CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == snapshot(name='custom config')
        assert Path(ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').resolve() == Path(
            CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg'
        )

    def test_generate_existing(
        self,
        generator: Xash3dFwgsGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg', contents='user stuff\n')
        fs.create_file(ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg', contents='gamepad stuff\n')
        fs.create_file(CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg', contents='custom stuff\n')
        fs.create_file(ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg', contents='custom stuff as well\n')
        fs.create_dir(ROMS / 'xash3d_fwgs' / 'rom' / 'save')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'xash3d_fwgs' / 'rom.game',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'userconfig.cfg').read_text() == 'user stuff\n'
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'gamepad.cfg').read_text() == 'gamepad stuff\n'
        assert (CONFIGS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == 'custom stuff\n'
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'custom.cfg').read_text() == 'custom stuff as well\n'
        assert (ROMS / 'xash3d_fwgs' / 'rom' / 'save').is_dir()
