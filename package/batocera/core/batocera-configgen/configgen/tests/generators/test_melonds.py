from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.melonds.melondsGenerator import MelonDSGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestMelonDSGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[MelonDSGenerator]:
        return MelonDSGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'nds'

    @pytest.fixture
    def emulator(self) -> str:
        return 'melonds'

    def test_generate(
        self,
        generator: MelonDSGenerator,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'nds' / 'rom.nds',
                two_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'melonDS' / 'melonDS.toml').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: MelonDSGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'melonDS' / 'melonDS.toml',
            contents="""
MouseHide = true
Foo = "bar"

[DS]
FirmwarePath = "/some/place/for/bios/firmware.bin"

[DLDI]
FolderPath = "/some/place/for/saves/nds"

[3D.GL]
BetterPolygons = true
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'melonDS' / 'melonDS.toml').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'melonds_renderer': '0'},
            {'melonds_vsync': 'True'},
            {'melonds_cheats': 'True'},
            {'melonds_framerate': 'False'},
            {'melonds_resolution': '2'},
            {'melonds_resolution': '3'},
            {'melonds_polygons': 'True'},
            {'melonds_polygons': 'False'},
            {'melonds_rotation': '1'},
            {'melonds_screenswap': 'True'},
            {'melonds_layout': '1'},
            {'melonds_screensizing': '1'},
            {'melonds_scaling': 'True'},
            {'melonds_osd': 'True'},
            {'melonds_console': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: MelonDSGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'melonDS' / 'melonDS.toml').read_text() == snapshot
