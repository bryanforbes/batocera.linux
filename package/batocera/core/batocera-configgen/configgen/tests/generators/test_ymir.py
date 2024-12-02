from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.config import SystemConfig
from configgen.generators.ymir.ymirGenerator import YmirGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestYmirGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[YmirGenerator]:
        return YmirGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'saturn'

    @pytest.fixture
    def emulator(self) -> str:
        return 'ymir'

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 16 / 9),
            ({'ymir_aspect': '1.3333333333333333'}, 4 / 3),
            ({'ymir_aspect': '1.5'}, 16 / 9),
            ({'ymir_aspect': '1.6'}, 16 / 9),
            ({'ymir_aspect': '1.7777777777777778'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: YmirGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    def test_generate(
        self,
        generator: YmirGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'saturn' / 'rom.cue',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'ymir').is_dir()
        assert (CONFIGS / 'ymir' / 'Ymir.toml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: YmirGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'ymir' / 'Ymir.toml',
            contents="""[General]
BoostEmuThreadPriority = true
BoostProcessPriority = true
EnableRewindBuffer = false
PauseWhenUnfocused = false
PreloadDiscImagesToRAM = false
RewindCompressionLevel = 12

[System]
AutoDetectRegion = true

[Video]
AutoResizeWindow = true
Deinterlace = false
FullScreen = false
ForceAspectRatio = true
DisplayVideoOutputInWindow = true
ForcedAspect = 0

[General.PathOverrides]
BackupMemory = "1"
Dumps = "2"
ExportedBackups = "3"
IPLROMImages = "/userdata/bios/foo"
PersistentState = "4"
ROMCartImages = "/userdata/roms/blah"
SaveStates = "/userdata/saves/asdf"
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'saturn' / 'rom.cue',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'ymir' / 'Ymir.toml').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'ymir_aspect': '1.3333333333333333'},
            {'ymir_aspect': '1.5'},
            {'ymir_aspect': '1.6'},
            {'ymir_aspect': '1.7777777777777778'},
            {'ymir_rotation': 'Normal'},
            {'ymir_rotation': '90CW'},
            {'ymir_interlace': '0'},
            {'ymir_interlace': '1'},
            {'ymir_meshes': '0'},
            {'ymir_meshes': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: YmirGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'saturn' / 'rom.cue',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'ymir' / 'Ymir.toml').read_text() == snapshot(name='config')

    def test_generate_controllers(
        self,
        generator: YmirGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        ds4_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'saturn' / 'rom.cue',
            make_player_controller_list(generic_xbox_pad, ps3_controller, ds4_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'ymir' / 'Ymir.toml').read_text() == snapshot(name='config')
