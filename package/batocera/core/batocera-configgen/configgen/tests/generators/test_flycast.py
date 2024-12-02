from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, DEFAULTS_DIR, SAVES
from configgen.generators.flycast.flycastGenerator import FlycastGenerator
from tests.generators.conftest import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestFlycastGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'dreamcast'

    @pytest.fixture
    def emulator(self) -> str:
        return 'flycast'

    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(DEFAULTS_DIR / 'data' / 'dreamcast' / 'vmu_save_blank.bin', contents='blank vmu')
        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert FlycastGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            FlycastGenerator().generate(
                mock_system,
                '/userdata/roms/dreamcast/rom.chd',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A1.bin').is_file()
        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A2.bin').is_file()
        assert (CONFIGS / 'flycast' / 'emu.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'flycast' / 'mappings' / 'SDL_real name 1.cfg').read_text() == snapshot(name='p1-mapping')

    @pytest.mark.system_name('naomi')
    def test_generate_arcade(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            FlycastGenerator().generate(
                mock_system,
                '/userdata/roms/dreamcast/rom.chd',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A1.bin').is_file()
        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A2.bin').is_file()
        assert (CONFIGS / 'flycast' / 'emu.cfg').read_text() == snapshot(name='config')
        assert (CONFIGS / 'flycast' / 'mappings' / 'SDL_real name 1_arcade.cfg').read_text() == snapshot(
            name='p1-mapping'
        )

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'flycast' / 'emu.cfg',
            contents="""[input]
device1 = 0

[config]
rend.Resolution = 2

[window]
fullscreen = no

[achievements]
Enabled = yes

[foo]
bar = baz
""",
        )
        fs.create_file(SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A1.bin', contents='existing a1 vmu')
        fs.create_file(SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A2.bin', contents='existing a2 vmu')

        FlycastGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A1.bin').read_text() == 'existing a1 vmu'
        assert (SAVES / 'dreamcast' / 'flycast' / 'vmu_save_A2.bin').read_text() == 'existing a2 vmu'
        assert (CONFIGS / 'flycast' / 'emu.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'flycast_render_resolution': '960'},
            {'flycast_ratio': 'yes'},
            {'flycast_rotate': 'yes'},
            {'flycast_sorting': '2'},
            {'flycast_sorting': '3'},
            {'flycast_renderer': '4'},
            {'flycast_renderer': '4', 'flycast_sorting': '3'},
            {'flycast_renderer': '0'},
            {'flycast_renderer': '0', 'flycast_sorting': '3'},
            {'flycast_anisotropic': '4'},
            {'flycast_language': '2'},
            {'flycast_region': '2'},
            {'flycast_loadstate': 'yes'},
            {'flycast_savestate': 'yes'},
            {'flycast_winCE': 'yes'},
            {'flycast_DSP': 'yes'},
            {'flycast_lightgun1_crosshair': 'Red'},
            {'flycast_lightgun1_crosshair': 'Blue'},
            {'flycast_lightgun1_crosshair': 'Green'},
            {'flycast_lightgun1_crosshair': 'White'},
            {'flycast_lightgun2_crosshair': 'Red'},
            {'flycast_lightgun2_crosshair': 'Blue'},
            {'flycast_lightgun2_crosshair': 'Green'},
            {'flycast_lightgun2_crosshair': 'White'},
            {'flycast_lightgun3_crosshair': 'Red'},
            {'flycast_lightgun3_crosshair': 'Blue'},
            {'flycast_lightgun3_crosshair': 'Green'},
            {'flycast_lightgun3_crosshair': 'White'},
            {'flycast_lightgun4_crosshair': 'Red'},
            {'flycast_lightgun4_crosshair': 'Blue'},
            {'flycast_lightgun4_crosshair': 'Green'},
            {'flycast_lightgun4_crosshair': 'White'},
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.password': 'password',
                'retroachievements.hardcore': '1',
                'retroachievements.token': 'token',
            },
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.password': 'password',
                'retroachievements.hardcore': '0',
                'retroachievements.token': 'token',
            },
            {'flycast_render_resolution': '960', 'flycast.config.rend.Resolution': '1200', 'flycast.foo.bar': 'baz'},
            {'flycast_ctrl1_pack': '3'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        FlycastGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'flycast' / 'emu.cfg').read_text() == snapshot

    @pytest.mark.parametrize('system_name', ['dreamcast', 'naomi'])
    def test_generate_controllers(
        self,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        gpio_controller_1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        FlycastGenerator().generate(
            mock_system,
            '/userdata/roms/dreamcast/rom.chd',
            make_player_controller_dict(generic_xbox_pad, ps3_controller, gpio_controller_1),
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'flycast' / 'emu.cfg').read_text() == snapshot
