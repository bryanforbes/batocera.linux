from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.hypseus_singe.hypseusSingeGenerator import HypseusSingeGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator
    from configgen.types import Resolution


class TestHypseusSingeGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return HypseusSingeGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'daphne'

    @pytest.fixture
    def emulator(self) -> str:
        return 'hypseus-singe'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem, mock_system: Emulator) -> FakeFilesystem:
        fs.create_file(
            ROMS / mock_system.name / 'ace.daphne' / 'ace.txt',
            contents="""
.
8123 ace.m2v
""",
        )
        fs.create_file(ROMS / mock_system.name / 'ace.daphne' / 'ace.m2v', contents='video file')
        fs.create_file('/usr/share/hypseus-singe/hypinput_gamepad.ini', contents='# gamepad config\n')
        fs.create_file('/usr/share/hypseus-singe/pics/annunon.png')
        fs.create_file('/usr/share/hypseus-singe/pics/subdir/sub_annunon.png')
        fs.create_file('/usr/share/hypseus-singe/sound/ab_alarm1.wav')
        fs.create_file('/usr/share/hypseus-singe/fonts/daphne.ttf')
        fs.create_file('/usr/share/hypseus-singe/bezels/ace.png')
        fs.create_file('/usr/share/hypseus-singe/bezels/default.png')
        return fs

    @pytest.fixture(autouse=True)
    def ffmpeg_probe(self, mocker: MockerFixture, request: SubRequest) -> Mock:
        param: tuple[int, int] | None = getattr(request, 'param', None)
        return mocker.patch(
            'ffmpeg.probe',
            return_value={
                'streams': [
                    {'width': 1024, 'height': 768, 'display_aspect_ratio': '0:0', 'codec_type': 'video'}
                    if param is None
                    else {'width': param[0], 'height': param[1], 'display_aspect_ratio': '0:0', 'codec_type': 'video'}
                ]
                if not param or param != (0, 0)
                else []
            },
        )

    @pytest.fixture(autouse=True)
    def guns_borders_size_name(self, mocker: MockerFixture, mock_system: Emulator, request: SubRequest) -> Mock:
        return mocker.patch.object(mock_system, 'guns_borders_size_name', return_value=getattr(request, 'param', None))

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'hypseus_ratio': 'force_ratio'}, 4 / 3),
            ({'hypseus_ratio': 'stretch'}, 16 / 9),
            ({'hypseus_ratio': 'original'}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: Generator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig(mock_system_config), {'width': 0, 'height': 0}, Path()) == result

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        ffmpeg_probe: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hypseus-singe' / 'hypinput.ini').read_text() == snapshot(name='config')
        assert ffmpeg_probe.call_args_list == snapshot(name='ffmpeg_probe')

        assert filecmp.cmp(CONFIGS / 'hypseus-singe' / 'hypinput.ini', CONFIGS / 'hypseus-singe' / 'custom.ini')
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png', '/usr/share/hypseus-singe/pics/annunon.png'
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'pics' / 'subdir' / 'sub_annunon.png',
            '/usr/share/hypseus-singe/pics/subdir/sub_annunon.png',
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav', '/usr/share/hypseus-singe/sound/ab_alarm1.wav'
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf', '/usr/share/hypseus-singe/fonts/daphne.ttf'
        )
        assert filecmp.cmp(CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png', '/usr/share/hypseus-singe/bezels/ace.png')

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'hypseus-singe' / 'hypinput_gamepad.ini', contents='# existing gamepad config\n')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'custom.ini', contents='# custom config\n')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png', contents='png')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav', contents='wav')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf', contents='ttf')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png', contents='png')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert filecmp.cmp(CONFIGS / 'hypseus-singe' / 'hypinput.ini', '/usr/share/hypseus-singe/hypinput_gamepad.ini')
        assert (CONFIGS / 'hypseus-singe' / 'custom.ini').read_text() == '# custom config\n'
        assert not filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png', '/usr/share/hypseus-singe/pics/annunon.png'
        )
        assert not filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav', '/usr/share/hypseus-singe/sound/ab_alarm1.wav'
        )
        assert not filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf', '/usr/share/hypseus-singe/fonts/daphne.ttf'
        )
        assert not filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png', '/usr/share/hypseus-singe/bezels/ace.png'
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_existing_older(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png', contents='png')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav', contents='wav')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf', contents='ttf')
        fs.create_file(CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png', contents='png')
        fs.utime(str(CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png'), times=(0, 0))
        fs.utime(str(CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav'), times=(0, 0))
        fs.utime(str(CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf'), times=(0, 0))
        fs.utime(str(CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png'), times=(0, 0))

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'pics' / 'annunon.png', '/usr/share/hypseus-singe/pics/annunon.png'
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'sound' / 'ab_alarm1.wav', '/usr/share/hypseus-singe/sound/ab_alarm1.wav'
        )
        assert filecmp.cmp(
            CONFIGS / 'hypseus-singe' / 'fonts' / 'daphne.ttf', '/usr/share/hypseus-singe/fonts/daphne.ttf'
        )
        assert filecmp.cmp(CONFIGS / 'hypseus-singe' / 'bezels' / 'ace.png', '/usr/share/hypseus-singe/bezels/ace.png')

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_commands_file(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'ace.daphne' / 'ace.commands', contents='-one 1 -two 2\n')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
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
            {'hypseus_joy': '0'},
            {'hypseus_joy': '1'},
            {'hypseus_api': 'OpenGL'},
            {'hypseus_api': 'Vulkan'},
            {'hypseus_filter': '0'},
            {'hypseus_filter': '1'},
            {'hypseus_axis': '0'},
            {'hypseus_axis': '1'},
            {'hypseus_rotate': '0'},
            {'hypseus_rotate': '90'},
            {'hypseus_rotate': '270'},
            {'hypseus_scanlines': '0'},
            {'hypseus_scanlines': '2'},
            {'hypseus_texturestream': '0'},
            {'hypseus_texturestream': '1'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_config(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('singe')
    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'singe_sprites': '0'},
            {'singe_sprites': '1'},
            {'singe_abs': '0'},
            {'singe_abs': '1'},
            {'singe_joystick_range': '5'},
        ],
        ids=str,
    )
    def test_generate_singe_config(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'singe' / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        ('bezel_name', 'rom_name'),
        [
            (bezel_name, rom_name)
            for bezel_name, rom_names in {
                'ace': ['ace', 'ace_a', 'ace_a2', 'ace91', 'ace91_euro', 'aceeuro'],
                'astron': ['astron', 'astronp'],
                'badlands': ['badlands', 'badlandsp'],
                'bega': ['bega', 'begar1'],
                'captainpower': ['cpower1', 'cpower2', 'cpower3', 'cpower4', 'cpowergh'],
                'cliff': ['cliffhanger', 'cliff', 'cliffalt', 'cliffalt2'],
                'cobra': ['cobra', 'cobraab', 'cobraconv', 'cobram3'],
                'conan': ['conan', 'future_boy'],
                'chantze_hd': ['chantze_hd', 'triad_hd', 'triadstone'],
                'crimepatrol': ['crimepatrol', 'crimepatrol-hd', 'cp_hd'],
                'dragon': ['dragon', 'dragon_trainer'],
                'drugwars': ['drugwars', 'drugwars-hd', 'cp2dw_hd'],
                'daitarn': ['daitarn', 'daitarn_3'],
                'dle': ['dle', 'dle_alt'],
                'fire_and_ice': ['fire_and_ice', 'fire_and_ice_v2'],
                'galaxy': ['galaxy', 'galaxyp'],
                'lair': [
                    'lair',
                    'lair_a',
                    'lair_b',
                    'lair_c',
                    'lair_d',
                    'lair_d2',
                    'lair_e',
                    'lair_f',
                    'lair_ita',
                    'lair_n1',
                    'lair_x',
                    'laireuro',
                ],
                'lbh': ['lbh', 'lbh-hd', 'lbh_hd'],
                'maddog': ['maddog', 'maddog-hd', 'maddog_hd'],
                'maddog2': ['maddog2', 'maddog2-hd', 'maddog2_hd'],
                'jack': ['jack', 'samurai_jack'],
                'johnnyrock': ['johnnyrock', 'johnnyrock-hd', 'johnnyrocknoir', 'wsjr_hd'],
                'pussinboots': ['pussinboots', 'puss_in_boots'],
                'spacepirates': ['spacepirates', 'spacepirates-hd', 'space_pirates_hd'],
            }.items()
            for rom_name in rom_names
        ],
    )
    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_bezel_lookup(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        bezel_name: str,
        rom_name: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.remove_object('/usr/share/hypseus-singe/bezels/ace.png')
        fs.remove_object(str(ROMS / mock_system.name / 'ace.daphne'))

        fs.create_file(f'/usr/share/hypseus-singe/bezels/{bezel_name}.png')
        fs.create_file(
            ROMS / mock_system.name / f'{rom_name}.daphne' / f'{rom_name}.txt',
            contents=f"""
.
8123 {rom_name}.m2v
""",
        )
        fs.create_file(ROMS / mock_system.name / f'{rom_name}.daphne' / f'{rom_name}.m2v', contents='video file')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / f'{rom_name}.daphne',
                [],
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
            {'hypseus_bezels': '0'},
            {'hypseus_bezels': '1'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_bezel_config(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_unknown_bezel(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/share/hypseus-singe/bezels/foobarbaz.png')
        fs.create_file(
            ROMS / mock_system.name / 'foobarbaz.daphne' / 'foobarbaz.txt',
            contents="""
.
8123 foobarbaz.m2v
""",
        )
        fs.create_file(ROMS / mock_system.name / 'foobarbaz.daphne' / 'foobarbaz.m2v', contents='video file')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'foobarbaz.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_missing_bezel(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.remove('/usr/share/hypseus-singe/bezels/ace.png')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_aspect_ratio_no_bezel(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.remove('/usr/share/hypseus-singe/bezels/ace.png')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1272},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_video_in_subdir(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.remove(str(ROMS / mock_system.name / 'ace.daphne' / 'ace.m2v'))
        fs.create_file(ROMS / mock_system.name / 'ace.daphne' / 'subdir' / 'ace.m2v', contents='video file')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_calculate_from_aspect_ratio(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        ffmpeg_probe: Mock,
    ) -> None:
        ffmpeg_probe.return_value = {
            'streams': [{'width': 20, 'height': 768, 'display_aspect_ratio': '4:3', 'codec_type': 'video'}]
        }

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    def test_generate_no_video_streams(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        ffmpeg_probe: Mock,
    ) -> None:
        ffmpeg_probe.return_value = {'streams': [{'codec_type': 'audio'}]}

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    @pytest.mark.mock_system_config({'hypseus_ratio': 'stretch'})
    def test_generate_config_stretch(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('resolution', [{'width': 1920, 'height': 1080}, {'width': 1920, 'height': 1440}], ids=str)
    @pytest.mark.parametrize('system_name', ['daphne', 'singe'])
    @pytest.mark.mock_system_config({'hypseus_ratio': 'force_ratio'})
    def test_generate_config_force_ratio(
        self,
        generator: Generator,
        resolution: Resolution,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                resolution,
            )
            == snapshot
        )

    @pytest.mark.parametrize('mock_system_config', [{}, {'singe_crosshair': '0'}, {'singe_crosshair': '1'}], ids=str)
    @pytest.mark.system_name('singe')
    def test_generate_guns_crosshair(
        self,
        generator: Generator,
        mocker: MockerFixture,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [mocker.Mock()],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        ('mock_system_config', 'resolution', 'ffmpeg_probe'),
        [
            ({'hypseus_ratio': 'stretch'}, {'width': 1920, 'height': 1080}, None),
            ({'hypseus_ratio': 'stretch'}, {'width': 1920, 'height': 1430}, None),
            ({'hypseus_ratio': 'force_ratio'}, {'width': 1920, 'height': 1080}, None),
            ({}, {'width': 1920, 'height': 1080}, (1920, 1430)),
            ({}, {'width': 1920, 'height': 1080}, (1920, 1429)),
            ({}, {'width': 1920, 'height': 1430}, (0, 0)),
            ({}, {'width': 1920, 'height': 1429}, (0, 0)),
        ],
        ids=str,
        indirect=['ffmpeg_probe'],
    )
    @pytest.mark.system_name('singe')
    def test_generate_guns_xratio(
        self,
        generator: Generator,
        mocker: MockerFixture,
        resolution: Resolution,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [mocker.Mock()],
                {},
                resolution,
            )
            == snapshot
        )

    @pytest.mark.parametrize('borders_color', [None, 'white', 'red', 'green', 'blue'])
    @pytest.mark.parametrize('guns_borders_size_name', ['thin', 'medium', 'big'], indirect=True)
    @pytest.mark.system_name('singe')
    def test_generate_border_color(
        self,
        generator: Generator,
        borders_color: str | None,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        if borders_color:
            mock_system.config['controllers.guns.borderscolor'] = borders_color

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'ace.daphne',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
