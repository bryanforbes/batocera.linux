from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final
from zipfile import ZipFile

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.openmsx.openmsxGenerator import OpenmsxGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


_DATA_DIR: Final = Path(__file__).parent.parent.parent.parent.parent.parent / 'emulators' / 'openmsx'


class TestOpenmsxGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenmsxGenerator]:
        return OpenmsxGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'msx1'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openmsx'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.add_real_file(_DATA_DIR / 'settings.xml', target_path='/usr/share/openmsx/settings.xml')
        return fs

    def test_has_internal_mangohud_call(self, generator: OpenmsxGenerator) -> None:  # pyright: ignore
        assert generator.hasInternalMangoHUDCall()

    def test_generate(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom (foo) [bar].cas',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openmsx' / 'share' / 'settings.xml').read_text() == snapshot(name='xml')
        assert (CONFIGS / 'openmsx' / 'share' / 'script.tcl').read_text() == snapshot(name='tcl')

    @pytest.mark.parametrize('system_name', ['msx2', 'msx2+', 'msxturbor', 'colecovision', 'spectravideo'])
    def test_generate_system(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.cas',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'openmsx_loading': 'false'},
            {'hud': 'game'},
            {'hud': ''},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom.cas',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openmsx' / 'share' / 'settings.xml').read_text() == snapshot(name='xml')

    def test_generate_controllers(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'msx1' / 'rom.cas',
            make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openmsx' / 'share' / 'script.tcl').read_text() == snapshot(name='tcl')

    def test_generate_laserdisc(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom.ogv',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('mock_system_config', [{'openmsx_disk': 'disk'}, {'openmsx_disk': 'hda'}], ids=str)
    def test_generate_disk(
        self,
        generator: OpenmsxGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom.dsk',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['cas', 'dsk', 'ogv'])
    def test_generate_zip(
        self,
        generator: OpenmsxGenerator,
        extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/msx1')
        with ZipFile('/userdata/roms/msx1/rom.zip', 'w') as zip:
            zip.writestr('thing.txt', 'text file')
            zip.writestr(f'rom.{extension}', 'rom')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('extension', ['rom', 'dsk'])
    def test_generate_openmsx_rom(
        self,
        generator: OpenmsxGenerator,
        extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/msx1/rom.openmsx', contents=f'one.{extension}\ntwo.{extension}\n')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'msx1' / 'rom.openmsx',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
