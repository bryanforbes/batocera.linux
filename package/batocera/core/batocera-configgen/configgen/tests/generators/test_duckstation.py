from __future__ import annotations

import itertools
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS
from configgen.exceptions import BatoceraException
from configgen.generators.duckstation.duckstationGenerator import DuckstationGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs', 'os_environ_lang')
class TestDuckstationGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DuckstationGenerator]:
        return DuckstationGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'psx'

    @pytest.fixture
    def emulator(self) -> str:
        return 'duckstation'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem, request: SubRequest) -> FakeFilesystem:
        fs.create_dir('/usr/share/duckstation/resources')

        if 'no_fs_mods' not in request.keywords:
            fs.create_file(BIOS / 'scph5501.bin')

        return fs

    @pytest.fixture(autouse=True)
    def remove_wayland(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv('WAYLAND_DISPLAY', raising=False)

    def test_generate(
        self,
        generator: DuckstationGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')
        assert Path('/usr/share/duckstation/resources/gamecontrollerdb.txt').read_text() == snapshot(
            name='controllerdb'
        )

    def test_generate_qt(
        self,
        generator: DuckstationGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/bin/duckstation-qt')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_wayland(
        self,
        generator: DuckstationGenerator,
        monkeypatch: pytest.MonkeyPatch,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        monkeypatch.setenv('WAYLAND_DISPLAY', '1')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_existing(
        self,
        generator: DuckstationGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'duckstation' / 'settings.ini',
            contents="""[Main]
SettingsVersion = 2

[ControllerPorts]
ControllerSettingsMigrated = false

[Console]
Region = NTSC-U

[BIOS]
SearchDirectory = /other/bios

[CPU]
ExecutionMode = Interpreter

[GPU]
Renderer = Software

[Display]
AspectRatio = 4:3

[Audio]
StretchMode = Resample

[GameList]
RecursivePaths = /other/roms/psx

[Cheevos]
Enabled = true

[TextureReplacements]
EnableVRAMWriteReplacements = false

[InputSources]
SDL = false

[MemoryCards]
Directory = /tmp

[Folders]
Cache = /tmp/duckstation

[Pad1]
Type = AnalogJoystick

[Hotkeys]
FastForward = Keyboard/F6
OpenQuickMenu = true

[CDROM]
AllowBootingWithoutSBIFile = true

[UI]
UnofficialBuildWarningConfirmed = false

[Foo]
Bar = baz
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')

    def test_generate_m3u(
        self,
        generator: DuckstationGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/userdata/roms/psx/rom.m3u',
            contents="""rom/rom1.chd
rom/rom2.chd
/rom/rom3.chd
rom/rom4.chd
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.m3u',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')
        assert Path('/tmp/rom1.m3u').read_text() == snapshot(name='m3u')

    @pytest.mark.no_fs_mods
    def test_generate_no_bios_dir_raises(
        self, generator: DuckstationGenerator, mock_system: Emulator, one_player_controllers: Controllers
    ) -> None:
        with pytest.raises(BatoceraException, match=r'^Unable to read BIOS directory: /userdata/bios$'):
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.no_fs_mods
    def test_generate_no_bios_raises(
        self,
        generator: DuckstationGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_dir(BIOS)

        with pytest.raises(BatoceraException, match=r'^No PSX1 BIOS found$'):
            generator.generate(
                mock_system,
                ROMS / 'psx' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'duckstation_clocking': '1.25'},
            {'duckstation_hrr': 'true'},
            {'duckstation_rewind': '120'},
            {'duckstation_rewind': '90'},
            {'duckstation_rewind': '60'},
            {'duckstation_rewind': '30'},
            {'duckstation_rewind': '15'},
            {'duckstation_rewind': '10'},
            {'duckstation_rewind': '5'},
            {'duckstation_region': 'PAL'},
            {'duckstation_cheats': 'true'},
            {'duckstation_cheats': 'false'},
            {'duckstation_PatchFastBoot': 'true'},
            {'duckstation_executionmode': 'Interpreter'},
            {'duckstation_gfxbackend': 'Vulkan'},
            {'duckstation_threadedpresentation': 'true'},
            {'duckstation_resolution_scale': '2'},
            {'duckstation_widescreen_hack': 'true'},
            {'duckstation_60hz': 'true'},
            {'duckstation_texture_filtering': 'Nearest'},
            {'duckstation_texture_filtering': 'Bilinear'},
            {'duckstation_pgxp': 'false'},
            {'duckstation_truecolour': 'true'},
            {'duckstation_dithering': 'false'},
            {'duckstation_interlacing': 'true'},
            {'duckstation_antialiasing': '2'},
            {'duckstation_antialiasing': '2-ssaa'},
            {'duckstation_ratio': '4:3'},
            {'duckstation_ratio': '16:9'},
            {'duckstation_vsync': 'true'},
            {'duckstation_CropMode': 'Borders'},
            {'duckstation_osd': 'true'},
            {'duckstation_ofp': 'true'},
            {'duckstation_integer': 'true'},
            {'duckstation_linear': 'true'},
            {'duckstation_stretch': 'true'},
            {'duckstation_stretch': 'true', 'duckstation_integer': 'false'},
            {'duckstation_stretch': 'true', 'duckstation_integer': 'true'},
            {'duckstation_audio_mode': 'Resample'},
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.password': 'password',
                'retroachievements.token': 'token',
            },
            {
                'retroachievements': 'on',
                'retroachievements.username': 'username',
                'retroachievements.password': 'password',
                'retroachievements.hardcore': '1',
                'retroachievements.richpresence': '1',
                'retroachievements.challenge_indicators': '1',
                'retroachievements.leaderboards': '1',
                'retroachievements.token': 'token',
                'retroachievements.unofficial': '1',
            },
            {'duckstation_custom_textures': '0'},
            {'duckstation_custom_textures': 'preload'},
            {'duckstation_digitalmode': 'true'},
            {'duckstation_Controller1': 'AnalogController'},
            {'duckstation_Controller1': 'AnalogController', 'duckstation_digitalmode': 'true'},
            {'duckstation_Controller1': 'NeGcon'},
            {'duckstation_Controller1': 'PlayStationMouse'},
            {'duckstation_crosshair': '1'},
            {'duckstation_boot_without_sbi': 'true'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: DuckstationGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')

    @pytest.mark.parametrize('bios_filename', ['scph1001.bin', 'scph5502.bin', 'scph3000.bin', 'ps1_rom.bin'])
    def test_generate_bios(
        self,
        generator: DuckstationGenerator,
        fs: FakeFilesystem,
        bios_filename: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        (BIOS / 'scph5501.bin').unlink()
        fs.create_file(BIOS / bios_filename)

        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            'en_US',
            'de_DE',
            'fr_FR',
            'es_ES',
            'he_IL',
            'it_IT',
            'ja_JP',
            'nl_NL',
            'pl_PL',
            'pt_PT',
            'pt_BR',
            'ru_RU',
            'zh_CN',
            'en_GB',
        ],
        indirect=True,
    )
    def test_generate_lang(
        self,
        generator: DuckstationGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')

    @pytest.mark.parametrize(
        'controller_count',
        [
            2,
            4,
            9,
        ],
    )
    def test_generate_controllers(
        self,
        generator: DuckstationGenerator,
        controller_count: int,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            make_player_controller_list(*itertools.repeat(generic_xbox_pad, controller_count)),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')

    @pytest.mark.parametrize(
        ('mock_system_config', 'metadata'),
        [
            ({'use_guns': '0'}, {}),
            ({'use_guns': '1'}, {}),
            ({'use_guns': '1'}, {'gun_type': 'justifier'}),
            ({'use_guns': '1', 'duckstation_Controller1': 'GunCon'}, {}),
            ({'use_guns': '1', 'controllers.pedals1': 'x'}, {}),
        ],
    )
    def test_generate_guns(
        self,
        mocker: MockerFixture,
        generator: DuckstationGenerator,
        metadata: dict[str, Any],
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psx' / 'rom.chd',
            make_player_controller_list(*itertools.repeat(generic_xbox_pad, 5)),
            metadata,
            [mocker.Mock()],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'duckstation' / 'settings.ini').read_text() == snapshot(name='settings')
