from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.dxx_rebirth.dxx_rebirthGenerator import DXX_RebirthGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestDXX_RebirthGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DXX_RebirthGenerator]:
        return DXX_RebirthGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'dxx-rebirth'

    @pytest.fixture
    def emulator(self) -> str:
        return 'dxx-rebirth'

    def test_get_mouse_mode(self, generator: DXX_RebirthGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: DXX_RebirthGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    @pytest.mark.parametrize('rom_path', ['descent1/descent.d1x', 'descent2/descent.d2x'])
    def test_generate(
        self,
        generator: DXX_RebirthGenerator,
        rom_path: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'dxx-rebirth' / rom_path,
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / f'{rom_path[-3:]}-rebirth' / 'descent.cfg').read_text() == snapshot(name='config')

    def test_generate_raises(
        self,
        generator: DXX_RebirthGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        with pytest.raises(BatoceraException, match=r'^Unknown rom type: /userdata/roms/dxx-rebirth/foo.rom$'):
            generator.generate(
                mock_system,
                ROMS / 'dxx-rebirth' / 'foo.rom',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'rebirth_vsync': '1'},
            {'rebirth_filtering': '1'},
            {'rebirth_filtering': '2'},
            {'rebirth_anisotropy': '1'},
            {'rebirth_multisample': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: DXX_RebirthGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'd1x-rebirth' / 'descent.cfg',
            contents="""ResolutionX=1920
ResolutionY=1080
WindowMode=0
VSync=0
TexFilt=0
TexAnisotropy=0
Multisample=0
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'dxx-rebirth' / 'descent1' / 'descent.d1x',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'd1x-rebirth' / 'descent.cfg').read_text() == snapshot(name='config')
