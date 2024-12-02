from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any
from zipfile import ZipFile

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.amiberry.amiberryGenerator import AmiberryGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from collections.abc import Mapping

    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.usefixtures('fs')
class TestAmiberryGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return AmiberryGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'amiga1200'

    @pytest.fixture
    def emulator(self) -> str:
        return 'amiberry'

    @pytest.fixture
    def core(self) -> str:
        return 'A500'

    @pytest.fixture
    def mock_system_base_config(self, mock_system_base_config: Mapping[str, Any]) -> dict[str, Any]:
        return {**mock_system_base_config, 'showFPS': True}

    def test_generate_lha(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.lha',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert Path(CONFIGS / 'amiberry' / 'conf' / 'amiberry.conf').read_text() == snapshot(name='amiberry.conf')
        assert Path(CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'overlay.cfg').read_text() == snapshot(
            name='overlay.cfg'
        )
        assert Path(
            CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'inputs' / f'{one_player_controllers[0].real_name}.cfg'
        ).read_text() == snapshot(name='controller.cfg')

    def test_generate_hdf(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.hdf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_uae(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.uae',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['iso', 'cue', 'chd'])
    def test_generate_cd(
        self,
        generator: Generator,
        extension: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / f'rom.{extension}',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['adf', 'ipf'])
    def test_generate_disk(
        self,
        generator: Generator,
        extension: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / f'rom.{extension}',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_disk_x(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga500/rom1.adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga500/rom2.adf', contents='rom2')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom1.adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_disk_x_5(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga500/rom1.adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga500/rom2.adf', contents='rom2')
        fs.create_file('/userdata/roms/amiga500/rom3.adf', contents='rom3')
        fs.create_file('/userdata/roms/amiga500/rom4.adf', contents='rom4')
        fs.create_file('/userdata/roms/amiga500/rom5.adf', contents='rom5')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom1.adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_disk_0(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga500/rom0.adf', contents='rom0')
        fs.create_file('/userdata/roms/amiga500/rom1.adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga500/rom2.adf', contents='rom2')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom1.adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_disk_1_of_2(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga500/rom (Disk 1 of 2).adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga500/rom (Disk 2 of 2).adf', contents='rom2')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom (Disk 1 of 2).adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_disk_1_of_5(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/amiga500/rom (Disk 1 of 5).adf', contents='rom1')
        fs.create_file('/userdata/roms/amiga500/rom (Disk 2 of 5).adf', contents='rom2')
        fs.create_file('/userdata/roms/amiga500/rom (Disk 3 of 5).adf', contents='rom3')
        fs.create_file('/userdata/roms/amiga500/rom (Disk 4 of 5).adf', contents='rom4')
        fs.create_file('/userdata/roms/amiga500/rom (Disk 5 of 5).adf', contents='rom5')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom (Disk 1 of 5).adf',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['info', 'lha', 'adf'])
    def test_generate_zip(
        self,
        generator: Generator,
        extension: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/amiga500')
        with ZipFile('/userdata/roms/amiga500/rom.zip', 'w') as zip:
            zip.writestr(f'rom.{extension}', 'rom')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_zip_unknown(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/amiga500')
        with ZipFile('/userdata/roms/amiga500/rom.zip', 'w') as zip:
            zip.writestr('dir/rom.ipf', 'rom')
            zip.writestr('rom.ipf', 'rom')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_unknown(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.foo',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert Path(CONFIGS / 'amiberry' / 'conf' / 'amiberry.conf').read_text() == snapshot(name='amiberry.conf')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'showFPS': False},
            {'uimode': 'Kiosk'},
            {'uimode': 'Kid'},
            {'amiberry_flickerfixer': 'true'},
            {'amiberry_flickerfixer': 'false'},
            {'amiberry_auto_height': 'true'},
            {'amiberry_auto_height': 'false'},
            {'amiberry_linemode': 'none'},
            {'amiberry_linemode': 'scanlines'},
            {'amiberry_linemode': 'double'},
            {'amiberry_resolution': 'lores'},
            {'amiberry_resolution': 'superhires'},
            {'amiberry_resolution': 'hires'},
            {'amiberry_scalingmethod': 'automatic'},
            {'amiberry_scalingmethod': 'smooth'},
            {'amiberry_scalingmethod': 'pixelated'},
            {'amiberry_virtual_keyboard': '0'},
            {'amiberry_virtual_keyboard': '1'},
            {'amiberry_hires_keyboard': '0'},
            {'amiberry_hires_keyboard': '1'},
            {'amiberry_vkbd_language': 'UK'},
            {'amiberry_vkbd_transparency': '80'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.lha',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert Path(CONFIGS / 'amiberry' / 'conf' / 'amiberry.conf').read_text() == snapshot(name='amiberry.conf')
        assert Path(CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'overlay.cfg').read_text() == snapshot(
            name='overlay.cfg'
        )
        assert Path(
            CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'inputs' / f'{one_player_controllers[0].real_name}.cfg'
        ).read_text() == snapshot(name='controller.cfg')

    def test_generate_two_controllers(
        self,
        generator: Generator,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'amiga500' / 'rom.lha',
                two_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert Path(CONFIGS / 'amiberry' / 'conf' / 'amiberry.conf').read_text() == snapshot(name='amiberry.conf')
        assert Path(CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'overlay.cfg').read_text() == snapshot(
            name='overlay.cfg'
        )
        assert Path(
            CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'inputs' / f'{two_player_controllers[0].real_name}.cfg'
        ).read_text() == snapshot(name='controller1.cfg')
        assert Path(
            CONFIGS / 'amiberry' / 'conf' / 'retroarch' / 'inputs' / f'{two_player_controllers[1].real_name}.cfg'
        ).read_text() == snapshot(name='controller2.cfg')
