from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from configgen.batoceraPaths import CONFIGS, DATAINIT_DIR, ROMS
from configgen.config import SystemConfig
from configgen.generators.mupen.mupenGenerator import MupenGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import controller_fixture, make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator

_CORE_DIR: Final = Path(__file__).parents[5] / 'emulators' / 'mupen64plus' / 'mupen64plus-core'


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

    @controller_fixture("""
        <inputConfig type="joystick" deviceName="SWITCH CO.,LTD. Controller (Dinput)" deviceGUID="03000000632500007505000011010000">
                <input name="a" type="button" id="2" value="1" code="306" />
                <input name="b" type="button" id="1" value="1" code="305" />
                <input name="down" type="hat" id="0" value="4" />
                <input name="hotkey" type="button" id="4" value="1" code="308" />
                <input name="joystick1left" type="axis" id="0" value="-1" code=" 0" />
                <input name="joystick1up" type="axis" id="1" value="-1" code="1" />
                <input name="l2" type="button" id="0" value="1" code="304" />
                <input name="left" type="hat" id="0" value="8" />
                <input name="pagedown" type="button" id="5" value="1" code="309" />
                <input name="pageup" type="button" id="4" value="1" code="308" />
                <input name="r2" type="button" id="8" value="1" code="312" />
                <input name="right" type="hat" id="0" value="2" />
                <input name="select" type="button" id="6" value="1" code="310" />
                <input name="start" type="button" id="12" value="1" code="316" />
                <input name="up" type="hat" id="0" value="1" />
                <input name="x" type="button" id="9" value="1" code="313" />
                <input name="y" type="button" id="3" value="1" code="307" />
        </inputConfig>
""")
    def n64_controller_with_n64_mapping(self) -> Controller: ...

    @controller_fixture("""
    <inputConfig type="joystick" deviceName="stick" deviceGUID="19000000010000000100000000010000">
        <input name="a" type="button" id="3" value="1" code="304" />
        <input name="b" type="button" id="4" value="1" code="305" />
        <input name="down" type="button" id="12" value="1" code="545" />
        <input name="hotkey" type="button" id="2" value="1" code="278" />
        <input name="left" type="button" id="13" value="1" code="546" />
        <input name="pagedown" type="button" id="8" value="1" code="311" />
        <input name="pageup" type="button" id="7" value="1" code="310" />
        <input name="right" type="button" id="14" value="1" code="547" />
        <input name="select" type="button" id="9" value="1" code="314" />
        <input name="start" type="button" id="10" value="1" code="315" />
        <input name="up" type="button" id="11" value="1" code="544" />
        <input name="x" type="button" id="5" value="1" code="307" />
        <input name="y" type="button" id="6" value="1" code="308" />
    </inputConfig>
""")
    def stick_controller(self) -> Controller: ...

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
        assert (
            MupenGenerator().getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path())
            == result
        )

    @pytest.mark.parametrize('core', ['gliden64', 'glide64mk2', 'rice'])
    def test_generate(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'n64' / 'rom.z64',
                one_player_controllers,
                {},
                [],
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
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'n64dd' / 'rom.z64',
                one_player_controllers,
                {},
                [],
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
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'mupen64' / 'mupen64plus.cfg',
            contents="""[CoreEvents]
Version = 2
Joy Mapping Stop = "1"
Joy Mapping Save State = "2"
Joy Mapping Load State = "3"
Joy Mapping Screenshot = "4"
Joy Mapping Increment Slot = "5"
Joy Mapping Fast Forward = "6"
Joy Mapping Reset = "7"
Joy Mapping Pause = "8"

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
            ROMS / 'n64' / 'rom.z64',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_rotated(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            one_player_controllers,
            {},
            [],
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
            {'showFPS': True},
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
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'n64' / 'rom.z64',
                one_player_controllers,
                {},
                [],
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
        anbernic_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(gpio_controller_1, ps3_controller, generic_xbox_pad, anbernic_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('controller_number', [1, 2, 3, 4])
    def test_generate_controllers_n64_mapping(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        n64_controller_with_n64_mapping: Controller,
        controller_number: int,
        snapshot: SnapshotAssertion,
    ) -> None:
        mock_system.config[f'mupen64-controller{controller_number}'] = 'n64'
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(
                n64_controller_with_n64_mapping,
                n64_controller_with_n64_mapping,
                n64_controller_with_n64_mapping,
                n64_controller_with_n64_mapping,
            ),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_controllers_user_mapping(
        self,
        fs: FakeFilesystem,
        generator: MupenGenerator,
        mock_system: Emulator,
        n64_controller_with_n64_mapping: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'mupen64' / 'input.xml',
            contents="""
<inputList>
	<defaultInputList>
		<input name="AnalogPeak"     value="16384,16384" />
		<input name="a"        	     value="A Button" />
		<input name="b"        	     value="C Button R" />
	</defaultInputList>
	<n64InputList>
		<input name="AnalogPeak"     value="8192,8192" />
		<input name="start"    	     value="Z Trig" />
		<input name="select"   	     value="Start" />
	</n64InputList>
</inputList>
""",
        )
        mock_system.config['mupen64-controller2'] = 'n64'

        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(
                n64_controller_with_n64_mapping,
                n64_controller_with_n64_mapping,
            ),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('has_both_directions', [True, False])
    def test_generate_controllers_direction_buttons_for_axis(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        stick_controller: Controller,
        has_both_directions: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        if not has_both_directions:
            del stick_controller.inputs['down']
            del stick_controller.inputs['right']

        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(stick_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_controllers_hat_for_axis(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        xtension_2p_p1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(xtension_2p_p1),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_controllers_keyboard(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            make_player_controller_list(keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')

    def test_generate_wheel(
        self,
        generator: MupenGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'n64' / 'rom.z64',
            one_player_controllers,
            {},
            [],
            {'/dev/input/event1': {'isWheel': True}},  # pyright: ignore
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'mupen64' / 'mupen64plus.cfg').read_text() == snapshot(name='config')
