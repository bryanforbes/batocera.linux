from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from configgen.batoceraPaths import CONFIGS, DATAINIT_DIR
from configgen.generators.mupen.mupenGenerator import MupenGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_dict

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, ControllerMapping
    from configgen.Emulator import Emulator

_CORE_DIR: Final = (
    Path(__file__).parent.parent.parent.parent.parent.parent / 'emulators' / 'mupen64plus' / 'mupen64plus-core'
)


class TestMupenGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[MupenGenerator]:
        return MupenGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'n64'

    @pytest.fixture
    def emulator(self) -> str:
        return 'glide64mk2'

    @pytest.fixture
    def core(self) -> str:
        return 'gliden64mk2'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.add_real_file(
            _CORE_DIR / 'controllers' / 'input.xml',
            target_path=DATAINIT_DIR / 'system' / 'configs' / 'mupen64' / 'input.xml',
        )
        return fs

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'mupen64plus_ratio': '4/3'}, 4 / 3),
            ({'mupen64plus_ratio': '16/9'}, 16 / 9),
            ({'mupen64plus_ratio': '4/3', 'ratio': '16/9'}, 4 / 3),
            ({'ratio': '16/9'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: MupenGenerator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert MupenGenerator().getInGameRatio(mock_system_config, {'width': 0, 'height': 0}, '') == result

    @pytest.mark.parametrize('core', ['gliden64', 'glide64mk2', 'rice'])
    def test_generate(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/n64/rom.z64',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    @pytest.mark.system_name('n64dd')
    def test_generate_n64dd(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/n64dd/rom.z64',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: MupenGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'mupen64' / 'mupen64plus.cfg',
            contents="""[CoreEvents]
Version = 2

[Core]
Version = 2.02

[Audio-SDL]
AUDIO_SYNC = True

[Video-General]
Version = 2

[Video-Glide64mk2]
Version = 2

[Video-GLideN64]
AspectRatio = 1

[Video-Rice]
Version = 2

[64DD]
IPL-ROM = Foo

[Input-SDL-Control1]
Version = 3

[Input-SDL-Control2]
Version = 4

[Custom]
Foo = Bar
""",
        )
        generator.generate(
            mock_system,
            '/userdata/roms/n64/rom.z64',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_rotated(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/n64/rom.z64',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1080, 'height': 1920},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'state_filename': 'foo.state'},
            {'state_slot': 1},
            {'incrementalsavestates': '0'},
            {'incrementalsavestates': '1'},
            {'showFPS': 'true'},
            {'mupen64plus_DisableExtraMem': 'True'},
            {'mupen64plus_DisableExtraMem': 'False'},
            {'mupen64plus_AudioSync': 'True'},
            {'mupen64plus_AudioSync': 'False'},
            {'mupen64plus_AudioBuffer': 'Very High'},
            {'mupen64plus_AudioBuffer': 'High'},
            {'mupen64plus_AudioBuffer': 'Low'},
            {'mupen64plus_ratio': '16/9'},
            {'mupen64plus_ratio': '16/9', 'ratio': '4/3'},
            {'ratio': '16/9'},
            {'mupen64plus_ratio': '4/3'},
            {'mupen64plus_ratio': '4/3', 'ratio': '16/9'},
            {'ratio': '4/3'},
            {'mupen64plus_Mipmapping': '0'},
            {'mupen64plus_Mipmapping': '1'},
            {'mupen64plus_Mipmapping': '2'},
            {'mupen64plus_Mipmapping': '3'},
            {'mupen64plus_Anisotropic': '0'},
            {'mupen64plus_Anisotropic': '2'},
            {'mupen64plus_AntiAliasing': '0'},
            {'mupen64plus_AntiAliasing': '2'},
            {'mupen64plus_LoadHiResTextures': 'True'},
            {'mupen64plus_LoadHiResTextures': 'False'},
            {'mupen64plus_TextureEnhancement': '0'},
            {'mupen64plus_TextureEnhancement': '1'},
            {'mupen64plus_fb_read_always': '-1'},
            {'mupen64plus_fb_read_always': '1'},
            {'mupen64plus_frameskip': '0'},
            {'mupen64plus_frameskip': 'automatic'},
            {'mupen64plus_frameskip': '1'},
            {'mupen64plus.Video-Rice.TextureEnhancement': '9', 'mupen64plus.CustomSection.CustomKey': 'True'},
            {'mupen64-controller1': 'n64limited'},
            {'mupen64-sensitivity1': '1.5'},
            {'mupen64-sensitivity1': '0.5'},
            {'mupen64-deadzone1': '0.15'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/n64/rom.z64',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_controllers(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        gpio_controller_1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/n64/rom.z64',
            make_player_controller_dict(gpio_controller_1, ps3_controller, generic_xbox_pad),
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_wheel(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            '/userdata/roms/n64/rom.z64',
            one_player_controllers,
            {},
            {},
            {'/dev/input/event1': {'isWheel': True}},  # pyright: ignore
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')
