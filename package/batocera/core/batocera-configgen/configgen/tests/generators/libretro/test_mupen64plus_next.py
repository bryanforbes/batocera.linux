from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pytest_lazy_fixtures import lf

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('mupen64plus-next')
@pytest.mark.fallback_system_name('n64')
class TestLibretroGeneratorMupen64PlusNext(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'mupen64plus-43screensize': ['320x240', '640x480']},
            {'mupen64plus-169screensize': ['640x360', '960x540']},
            {'mupen64plus-aspect': '16:9 adjusted', 'ratio': '16/9', 'bezel': 'none'},
            {'mupen64plus-BilinearMode': ['standard', '3point']},
            {'mupen64plus-MultiSampling': ['0', '2']},
            {'mupen64plus-txFilterMode': ['None', 'Smooth filtering 1']},
            {'mupen64plus-txEnhancementMode': ['None', 'As Is']},
            {'mupen64plus-rdpPlugin': 'parallel'},
            {'mupen64plus-rspPlugin': 'parallel'},
            {'mupen64plus-cpuCore': 'cached_interpreter'},
            {'mupen64plus-Framerate': 'Fullspeed'},
            {'mupen64plus-parallel-rdp-upscaling': '2x'},
            {'mupen64plus-sensitivity': '50'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    @pytest.mark.parametrize_core_configs([{'mupen64plus-controller1': ['retropad', 'n64', 'n64limited']}])
    def test_generate_controllers_config(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, ps3_controller, keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        'first_controller',
        [lf('n64_controller'), lf('nintendo_n64_controller'), lf('n64_modkit')],
    )
    @pytest.mark.parametrize_systems
    def test_generate_n64_first_controller(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        first_controller: Controller,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.z64')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / 'rom.z64',
            make_player_controller_list(first_controller, generic_xbox_pad, ps3_controller, keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        ('rumble_value', 'get_games_metadata'),
        [
            ('none', None),
            ('memory', None),
            ('rumble', None),
            ('auto_rumble', None),
            pytest.param('auto_rumble', {'controller_rumble': 'false'}, id='auto_rumble-false'),
            pytest.param('auto_rumble', {'controller_rumble': 'true'}, id='auto_rumble-true'),
        ],
        indirect=['get_games_metadata'],
    )
    @pytest.mark.parametrize('pack', [1, 2, 3, 4])
    @pytest.mark.parametrize_systems
    @pytest.mark.usefixtures('get_games_metadata')
    def test_generate_controllers_rumble(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        pack: int,
        rumble_value: str,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.z64')
        mock_system.config[f'mupen64plus-pak{pack}'] = rumble_value

        generator.generate(
            mock_system,
            ROMS / mock_system.name / 'rom.z64',
            make_player_controller_list(generic_xbox_pad, generic_xbox_pad, generic_xbox_pad, generic_xbox_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_core_config_matches(snapshot)

    @pytest.mark.parametrize('has_wheels', [True, False])
    @pytest.mark.parametrize('deadzone', [None, '30'])
    @pytest.mark.parametrize('use_wheels', [None, '0', '1'])
    def test_generate_wheels(
        self,
        generator: Generator,
        default_extension: str,
        use_wheels: str | None,
        deadzone: str | None,
        has_wheels: bool,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        if use_wheels is not None:
            mock_system.config['use_wheels'] = use_wheels

        if deadzone is not None:
            mock_system.config['mupen64plus-deadzone'] = deadzone

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {'foo': {}} if has_wheels else {},  # pyright: ignore
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)
