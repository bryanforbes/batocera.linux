from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import ZipFile

import pytest

from configgen.batoceraPaths import ROMS
from configgen.exceptions import BatoceraException
from configgen.generators.clk.clkGenerator import ClkGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestClkGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ClkGenerator]:
        return ClkGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'cplus4'

    @pytest.fixture
    def emulator(self) -> str:
        return 'clk'

    @pytest.mark.parametrize(
        'system_name',
        [
            'mastersystem',
            'colecovision',
            'atarist',
            'amstradcpc',
            'msx1',
            'msx2',
            'zxspectrum',
            'archimedes',
            'electron',
            'macintosh',
            'oricatmos',
        ],
    )
    def test_generate(
        self,
        fs: FakeFilesystem,
        generator: ClkGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.tzx')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.tzx',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_zip(
        self,
        fs: FakeFilesystem,
        generator: ClkGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/tmp/clk_extracted/rom.foo')
        fs.create_dir(ROMS / mock_system.name)
        with ZipFile(ROMS / mock_system.name / 'rom.zip', 'w') as zip:
            zip.writestr('rom.tzx', 'rom')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert Path('/tmp/clk_extracted/rom.tzx').exists()
        assert not Path('/tmp/clk_extracted/rom.foo').exists()

    def test_generate_rom_is_dir(
        self,
        fs: FakeFilesystem,
        generator: ClkGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_dir(ROMS / mock_system.name / 'rom.tzx')

        with pytest.raises(BatoceraException, match=r'^ROM is a directory: '):
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.tzx',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
