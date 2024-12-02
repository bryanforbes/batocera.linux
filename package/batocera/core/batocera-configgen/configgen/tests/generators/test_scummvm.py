from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.scummvm.scummvmGenerator import ScummVMGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestScummVMGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ScummVMGenerator]:
        return ScummVMGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'scummvm'

    @pytest.fixture
    def emulator(self) -> str:
        return 'scummvm'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 16 / 9),
            ({'scumm_stretch': 'even-pixels'}, 16 / 9),
            ({'scumm_stretch': 'fit_force_aspect'}, 4 / 3),
            ({'scumm_stretch': 'pixel-perfect'}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: ScummVMGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: ScummVMGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'scummvm' / 'rom.scummvm')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'scummvm' / 'rom.scummvm',
                two_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (BIOS / 'scummvm' / 'extra').is_dir()
        assert (CONFIGS / 'scummvm' / 'scummvm.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: ScummVMGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'scummvm' / 'rom.scummvm')
        fs.create_file(
            CONFIGS / 'scummvm' / 'scummvm.ini',
            contents="""[scummvm]
gui_browser_native = true

[foo]
bar = true
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'scummvm' / 'rom.scummvm',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'scummvm' / 'scummvm.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'scumm_scale': '7'},
            {'scumm_scaler_mode': 'hq'},
            {'scumm_stretch': 'even-pixels'},
            {'scumm_renderer': 'software'},
            {'scumm_language': 'en'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: ScummVMGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'scummvm' / 'rom.scummvm')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'scummvm' / 'rom.scummvm',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        ('rom', 'contents'),
        [
            ('/userdata/roms/scummvm/Monkey Island 2/Monkey Island 2.scummvm', 'monkey2'),
            ('/userdata/roms/scummvm/Monkey Island 2/Monkey Island 2.scummvm', 'scumm:monkey2'),
            ('/userdata/roms/scummvm/Monkey Island 2/monkey2.scummvm', ''),
            ('/userdata/roms/scummvm/Monkey Island 2/monkey2.scummvm', 'scumm:monkey2-cd-fr'),
            ('/tmp/Monkey Island 2/Monkey Island 2.scummvm', 'scumm:monkey2'),
            ('/tmp/Monkey Island 2/monkey2.scummvm', 'scumm:monkey2-cd-fr'),
            ('/tmp/Monkey Island 2/monkey2.scummvm', ''),
        ],
    )
    def test_generate_game_id(
        self,
        generator: ScummVMGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
        contents: str,
    ) -> None:
        fs.create_file(rom, contents=contents)

        assert (
            generator.generate(
                mock_system,
                Path(rom).parent if rom.startswith('/tmp') else Path(rom),
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        ('rom', 'contents'),
        [
            ('/userdata/roms/scummvm/Monkey Island 2/Monkey Island 2.scummvm', ''),
            ('/userdata/roms/scummvm/Monkey Island 2/Monkey Island 2.scummvm', 'Monkey Island'),
            ('/tmp/Monkey Island 2/Monkey Island 2.scummvm', ''),
            ('/tmp/Monkey Island 2/Monkey Island 2.scummvm', 'Monkey Island 2'),
            ('/tmp/Monkey Island 2/foo.txt', ''),
        ],
    )
    def test_generate_auto_detect(
        self,
        generator: ScummVMGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
        contents: str,
    ) -> None:
        fs.create_file(rom, contents=contents)

        assert (
            generator.generate(
                mock_system,
                Path(rom).parent if rom.startswith('/tmp') else Path(rom),
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
