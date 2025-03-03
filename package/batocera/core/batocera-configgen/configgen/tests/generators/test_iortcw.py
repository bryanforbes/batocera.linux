from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.iortcw.iortcwGenerator import IORTCWGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestIORTCWGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[IORTCWGenerator]:
        return IORTCWGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'iortcw'

    @pytest.fixture
    def emulator(self) -> str:
        return 'iortcw'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(ROMS / 'iortcw' / 'main')

        return fs

    def test_get_in_game_ratio(self, generator: IORTCWGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: IORTCWGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path(),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'iortcw' / 'main' / 'wolfconfig.cfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self, generator: IORTCWGenerator, fs: FakeFilesystem, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            ROMS / 'iortcw' / 'main' / 'wolfconfig.cfg',
            contents="""seta r_mode "1"
seta r_noborder "2"
seta r_fullscreen "3"
seta r_allowResize "1"
seta r_centerWindow "0"
seta r_inGameVideo "0"
seta r_customheight ""480""
seta r_customwidth ""640""
seta in_joystick "0"
seta in_joystickUseAnalog "0"
bind PAD0_A ""+flip""
bind PAD0_X ""+flip""
bind PAD0_Y ""+flip""
bind PAD0_B ""+flip""
bind PAD0_LEFTSHOULDER "flip"
bind PAD0_RIGHTSHOULDER "flip"
bind PAD0_LEFTSTICK_LEFT "+flip"
bind PAD0_LEFTSTICK_RIGHT "+flip"
bind PAD0_LEFTSTICK_UP "+flip"
bind PAD0_LEFTSTICK_DOWN "+flip"
bind PAD0_RIGHTSTICK_LEFT "+flip"
bind PAD0_RIGHTSTICK_RIGHT "+flip"
bind PAD0_RIGHTSTICK_UP "+flip"
bind PAD0_RIGHTSTICK_DOWN "+flip"
bind PAD0_LEFTTRIGGER "+flip"
bind PAD0_RIGHTTRIGGER "+flip"
seta cl_renderer "rend2"
seta r_swapInterval "1"
seta com_maxfps "10"
seta r_ext_texture_filter_anisotropic "1"
seta r_ext_max_anisotropy "8"
seta r_ext_multisample "1"
seta r_ext_framebuffer_multisample "1"
seta com_introplayed "1"
seta cl_language "3"
""",
        )
        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'iortcw' / 'main' / 'wolfconfig.cfg').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'iortcw_api': 'rend2'},
            {'iortcw_vsync': '0'},
            {'iortcw_vsync': '1'},
            {'iortcw_fps': '120'},
            {'iortcw_filtering': '4'},
            {'iortcw_aa': '2'},
            {'iortcw_skip_video': '0'},
            {'iortcw_skip_video': '1'},
            {'iortcw_language': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self, generator: IORTCWGenerator, mock_system: Emulator, snapshot: SnapshotAssertion
    ) -> None:
        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'iortcw' / 'main' / 'wolfconfig.cfg').read_text() == snapshot
