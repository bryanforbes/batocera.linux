from __future__ import annotations

import shutil
import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.model2emu.model2emuGenerator import Model2EmuGenerator
from tests.conftest import get_os_environ
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs', 'wine_runner')
class TestModel2EmuGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Model2EmuGenerator]:
        return Model2EmuGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'model2'

    @pytest.fixture
    def emulator(self) -> str:
        return 'model2emu'

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture) -> None:
        mocker.patch.dict(
            'os.environ',
            values={
                '__VK_LAYER_NV_optimus': '1',
                'FOO': 'BAR',
                '__NV_PRIME_RENDER_OFFLOAD': '1',
                '__GLX_VENDOR_LIBRARY_NAME': '1',
            },
            clear=True,
        )

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(
            '/usr/model2emu/EMULATOR.INI',
            contents=r""";Configuration file for the SEGA Model 2 emulator
;All text to the right of ; is ignored (use as comments)


;Add your rom directories here (max 10)
;ROMS subdirectory in the same folder than the exe is always scanned when searching for roms
;(remove the ; form Dir1)
[RomDirs]
Dir1=z:\userdata\roms\model2


[Renderer]
SoftwareVertexProcessing=0

Wireframe=0			;Disables polygon filling (for debug purposes, don't change)
FakeGouraud=0			;Tries to guess Per-vertex colour (gouraud) from the Model2 per-poly information (flat)
Bilinear=1			;Enables bilinear filtering of textures
Trilinear=0			;Enables mipmap usage and trilinear filtering (doesn't work with some games, DoA for example)
FilterTilemaps=0		;Enables bilinear filtering on tilemaps (looks good, but can cause some stretch artifacts)
ForceManaged=0			;Forces the DX driver to use Managed textures instead of Dynamic. Use it if the emulator
				;crashes after loading or doesn't show anything
ForceSync=0
FullScreenWidth=640
FullScreenHeight=480

AutoMip=0			;Enables Direct3D Automipmap generation
MeshTransparency=0		;Enabled meshed polygons for translucency. Requires PS3.0
DrawCross=1			;Show Crosshair in gun games
GammaR=1.0			;Per Component Gamma correction (1.0 = no correction). Red
GammaG=1.0			;Green
GammaB=1.0			;Blue

WideScreenWindow=0		;Set widescreen in windows mode: 0 - 4:3, 1 - 16:9, 2 - 16:10
FSAA=0				;Enable full screen antialiasing in Direct3D



;These options are configured from menus so don't touch
FullMode=0
Sound=1
Frameskip=-1
AutoFull=0
Filter=20373472



[Input]
XInput=0			;Enable support for Xbox360 compatible devices
EnableFF=0			;Enable Force Feedback Effects
HoldGears=0			;Set to 1 to return to Neutral in driving games when the gear shift key is released
UseRawInput=0			;Read mouse through Rawinput, allowing 2 mice
RawDevP1=0			;Assign specific RawInput devices to players. If you have more than 2 mice
RawDevP2=1			;set which one is assigned to each player (0-based)

;FORCE EFFECTS PARAMETERS
;FE_CENTERING Effect (Spring centering effect)
FE_CENTERING_Gain=0.5		;Global gain
FE_CENTERING_Coefficient=10000	;0-10000
FE_CENTERING_Saturation=10000	;0-10000
FE_CENTERING_Deadband=1000	;10%

;FE_CLUTCH Effect (Friction, wheel turn hardness)
FE_CLUTCH_Gain=1.0		;Global gain
FE_CLUTCH_Coefficient=10000	;0-10000

;FE_LEFT,FE_RIGHT (Constant force in a direction)
FE_LEFT_Gain=1.0		;Global gain
FE_LEFT_Magnitude=10000		;0-10000
FE_RIGHT_Gain=1.0		;Global gain
FE_RIGHT_Magnitude=10000	;0-10000


;FE_UNCENTERING (Sine force, wave the wheel, rumble)
FE_UNCENTERING_Gain=1.0		;Global gain
FE_UNCENTERING_Magnitude=10000	;0-10000
FE_UNCENTERING_Offset=-200
FE_UNCENTERING_Phase=0
FE_UNCENTERING_Period=56000

""",
        )
        fs.create_file('/usr/model2emu/scripts/common.lua', contents='common.lua')
        fs.create_file('/usr/model2emu/CFG/config.txt', contents='config.txt')
        fs.create_dir('/userdata/roms/model2')

        return fs

    def test_generate(
        self,
        generator: Model2EmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        wine_runner_install_wine_trick: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'model2' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert wine_runner_install_wine_trick.call_args_list == snapshot(name='winetricks')
        assert Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').read_text() == snapshot(
            name='config'
        )
        assert stat.filemode(
            Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').stat().st_mode
        ) == snapshot(name='config-mode')
        assert Path('/userdata/system/wine-bottles/model2/model2emu/scripts/common.lua').exists()
        assert Path('/userdata/system/wine-bottles/model2/model2emu/CFG/config.txt').exists()

    def test_generate_existing(
        self,
        generator: Model2EmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/system/wine-bottles/model2/xinput_cfg.done')
        fs.create_file(
            '/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI',
            contents=r"""[RomDirs]
Dir1=z:\userdata\roms\model2

[Renderer]
SoftwareVertexProcessing=0

[Input]
XInput=0

[Foo]
Bar = 1
""",
        )

        fs.create_file('/userdata/system/wine-bottles/model2/model2emu/scripts/common.lua', contents='new common.lua')
        fs.create_file('/userdata/system/wine-bottles/model2/model2emu/CFG/config.txt', contents='new config.txt')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'model2' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').read_text() == snapshot(
            name='config'
        )
        assert stat.filemode(
            Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').stat().st_mode
        ) == snapshot(name='config-mode')
        # scripts always get copied
        assert Path('/userdata/system/wine-bottles/model2/model2emu/scripts/common.lua').read_text() == 'common.lua'
        assert Path('/userdata/system/wine-bottles/model2/model2emu/CFG/config.txt').read_text() == 'new config.txt'

    def test_generate_config_rom(
        self,
        generator: Model2EmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path('config'),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'model2_renderRes': '1'},
            {'model2_fakeGouraud': '1'},
            {'model2_bilinearFiltering': '0'},
            {'model2_trilinearFiltering': '1'},
            {'model2_filterTilemaps': '1'},
            {'model2_forceManaged': '1'},
            {'model2_enableMIP': '1'},
            {'model2_meshTransparency': '1'},
            {'model2_fullscreenAA': '1'},
            {'model2_useRawInput': '1'},
            {'model2_crossHairs': '1'},
            {'model2_xinput': '1'},
            {'model2_forceFeedback': '1'},
            {'model2_Software': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Model2EmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'model2' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').read_text() == snapshot(
            name='config'
        )

    def test_generate_roms_dirs(
        self,
        generator: Model2EmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'model2' / 'foo')
        fs.create_dir(ROMS / 'model2' / 'images')
        fs.create_file(ROMS / 'model2' / 'bar')

        generator.generate(
            mock_system,
            ROMS / 'model2' / 'rom.zip',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').read_text() == snapshot(
            name='config'
        )

    @pytest.mark.parametrize(
        ('mock_system_config', 'needs_cross'),
        [
            pytest.param({}, False, id='no config, need_cross false'),
            pytest.param({}, True, id='no config, need_cross true'),
            pytest.param({'model2_crossHairs': '1'}, True, id='config crossHairs 1, need_cross true'),
            pytest.param({'model2_crossHairs': '0'}, True, id='config crossHairs 0, need_cross true'),
        ],
    )
    def test_generate_guns(
        self,
        mocker: MockerFixture,
        generator: Model2EmuGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        needs_cross: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'model2' / 'rom.zip',
            one_player_controllers,
            {},
            [mocker.Mock(needs_cross=needs_cross)],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').read_text() == snapshot(
            name='config'
        )

    def test_generate_nvidia(
        self,
        generator: Model2EmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'model2' / 'rom.zip',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert get_os_environ() == snapshot(name='environ')

    @pytest.mark.parametrize('existing_value', ['false', 'true'])
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'model2_ratio': 'False'},
            {'model2_ratio': 'True'},
        ],
        ids=str,
    )
    def test_generate_widescreen_script(
        self,
        generator: Model2EmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        existing_value: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/model2emu/scripts/rom.lua',
            contents=rf"""require("model2")

function Init()

	TestSurface = Video_CreateSurfaceFromFile("scripts\\scanlines_default.png");
	wide={existing_value}
	press=0
end

function Frame()
		if Input_IsKeyPressed(0x3F)==1 and press==0 then wide=not wide press=1
		elseif Input_IsKeyPressed(0x3F)==0 and press==1 then press=0
		end

	if wide==true then
		Model2_SetWideScreen(1)
	else
		Model2_SetWideScreen(0)
	end
end

function PostDraw()
		if Options.scanlines.value==1 then
		Video_DrawSurface(TestSurface,0,0);
	end

end

function health_1p_cheat_f(value)
        I960_WriteWord(RAMBASE+0x3CA0,1800); -- 1P full health
end

function health_2p_cheat_f(value)
        I960_WriteWord(RAMBASE+0x42A0,1800); -- 2P full health
end

Options =
{{
	health_1p_cheat={{name="1P Infinite Health",values={{"Off","On"}},runfunc=health_1p_cheat_f}},
	health_2p_cheat={{name="2P Infinite Health",values={{"Off","On"}},runfunc=health_2p_cheat_f}},
	scanlines={{name="Scanlines (50%)",values={{"Off","On"}}}}
}}
""",
        )

        # simulate the generator already being run
        shutil.copytree('/usr/model2emu', '/userdata/system/wine-bottles/model2/model2emu')
        Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').chmod(stat.S_IRWXO)

        generator.generate(
            mock_system,
            ROMS / 'model2' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/scripts/rom.lua').read_text() == snapshot

    @pytest.mark.parametrize('existing_value', [None, '0', '1'])
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'model2_scanlines': 'False'},
            {'model2_scanlines': 'True'},
        ],
        ids=str,
    )
    def test_generate_scanlines_script(
        self,
        generator: Model2EmuGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        existing_value: str | None,
        snapshot: SnapshotAssertion,
    ) -> None:
        options_line = '' if existing_value is None else f'\r\n\tOptions.scanlines.value={existing_value}'
        fs.create_file(
            '/usr/model2emu/scripts/rom.lua',
            contents=rf"""require("model2")

function Init()

	TestSurface = Video_CreateSurfaceFromFile("scripts\\scanlines_default.png");{options_line}
	wide=true
	press=0
end

function Frame()
		if Input_IsKeyPressed(0x3F)==1 and press==0 then wide=not wide press=1
		elseif Input_IsKeyPressed(0x3F)==0 and press==1 then press=0
		end

	if wide==true then
		Model2_SetWideScreen(1)
	else
		Model2_SetWideScreen(0)
	end
end

function PostDraw()
		if Options.scanlines.value==1 then
		Video_DrawSurface(TestSurface,0,0);
	end

end

function health_1p_cheat_f(value)
        I960_WriteWord(RAMBASE+0x3CA0,1800); -- 1P full health
end

function health_2p_cheat_f(value)
        I960_WriteWord(RAMBASE+0x42A0,1800); -- 2P full health
end

Options =
{{
	health_1p_cheat={{name="1P Infinite Health",values={{"Off","On"}},runfunc=health_1p_cheat_f}},
	health_2p_cheat={{name="2P Infinite Health",values={{"Off","On"}},runfunc=health_2p_cheat_f}},
	scanlines={{name="Scanlines (50%)",values={{"Off","On"}}}}
}}
""",
        )

        # simulate the generator already being run
        shutil.copytree('/usr/model2emu', '/userdata/system/wine-bottles/model2/model2emu')
        Path('/userdata/system/wine-bottles/model2/model2emu/EMULATOR.INI').chmod(stat.S_IRWXO)

        generator.generate(
            mock_system,
            ROMS / 'model2' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert Path('/userdata/system/wine-bottles/model2/model2emu/scripts/rom.lua').read_text() == snapshot
