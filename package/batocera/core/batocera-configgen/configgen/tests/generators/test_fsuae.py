from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.fsuae.fsuaeGenerator import FsuaeGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestFsuaeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[FsuaeGenerator]:
        return FsuaeGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'amiga1200'

    @pytest.fixture
    def emulator(self) -> str:
        return 'fsuae'

    @pytest.fixture
    def core(self) -> str:
        return 'A1200'

    @pytest.mark.parametrize('core', ['A500', 'A500+', 'A600', 'A1000', 'A3000', 'A1200', 'A4000', 'CD32', 'CDTV'])
    def test_generate(
        self,
        generator: FsuaeGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga1200' / 'rom.lha',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('core', ['A1200', 'CD32'])
    def test_generate_disk_x_5(
        self,
        generator: FsuaeGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga1200/rom1.adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga1200/rom2.adf', contents='rom2')
        fs.create_file('/userdata/roms/amiga1200/rom3.adf', contents='rom3')
        fs.create_file('/userdata/roms/amiga1200/rom4.adf', contents='rom4')
        fs.create_file('/userdata/roms/amiga1200/rom5.adf', contents='rom5')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga1200' / 'rom1.adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('core', ['A1200', 'CD32'])
    def test_generate_disk_0(
        self,
        generator: FsuaeGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga1200/rom0.adf', contents='rom0')
        fs.create_file('/userdata/roms/amiga1200/rom1.adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga1200/rom2.adf', contents='rom2')
        fs.create_file('/userdata/roms/amiga1200/rom3.adf', contents='rom3')
        fs.create_file('/userdata/roms/amiga1200/rom4.adf', contents='rom4')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga1200' / 'rom1.adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('core', ['A1200', 'CD32'])
    def test_generate_zip(
        self,
        generator: FsuaeGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/tmp/fsuae/foo.txt')
        fs.create_dir('/userdata/roms/amiga1200')

        with ZipFile('/userdata/roms/amiga1200/rom.zip', 'w') as zip:
            zip.writestr('rom1.ipf', 'rom1')
            zip.writestr('README.txt', 'readme')
            zip.writestr('rom2.adf', 'rom2')
            zip.writestr('rom3.dms', 'rom3')
            zip.writestr('rom4.adz', 'rom4')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga1200' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert not Path('/tmp/fsuae/foo.txt').exists()
        assert Path('/tmp/fsuae/README.txt').exists()
        assert Path('/tmp/fsuae/rom1.ipf').exists()
        assert Path('/tmp/fsuae/rom2.adf').exists()
        assert Path('/tmp/fsuae/rom3.dms').exists()
        assert Path('/tmp/fsuae/rom4.adz').exists()

    def test_generate_controllers(
        self,
        generator: FsuaeGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga1200' / 'rom.lha',
                make_player_controller_list(
                    generic_xbox_pad, ps3_controller, generic_xbox_pad, ps3_controller, generic_xbox_pad
                ),
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
