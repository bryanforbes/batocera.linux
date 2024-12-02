from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.dxx_rebirth.dxx_rebirthGenerator import DXX_RebirthGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestDXX_RebirthGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'dxx-rebirth'

    @pytest.fixture
    def emulator(self) -> str:
        return 'dxx-rebirth'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DXX_RebirthGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert DXX_RebirthGenerator().getMouseMode({}, '')

    def test_get_in_game_ratio(self) -> None:
        assert DXX_RebirthGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    @pytest.mark.parametrize('rom_path', ['descent1/descent.d1x', 'descent2/descent.d2x'])
    def test_generate(
        self,
        rom_path: str,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = DXX_RebirthGenerator().generate(
            mock_system,
            f'/userdata/roms/dxx-rebirth/{rom_path}',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / f'{rom_path[-3:]}-rebirth' / 'descent.cfg').read_text() == snapshot(name='config')

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
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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

        DXX_RebirthGenerator().generate(
            mock_system,
            '/userdata/roms/dxx-rebirth/descent1/descent.d1x',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'd1x-rebirth' / 'descent.cfg').read_text() == snapshot(name='config')
