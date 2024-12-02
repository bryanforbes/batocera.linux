from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NotRequired, TypedDict

import pytest
from syrupy.extensions.image import PNGImageSnapshotExtension

from configgen.batoceraPaths import DEFAULTS_DIR, ROMS
from configgen.exceptions import BatoceraException
from configgen.generators.mame.mameControllers import generatePadsConfig
from configgen.generators.mame.mameGenerator import MameGenerator
from configgen.generators.mame.mamePaths import MAME_CONFIG, MAME_DEFAULT_DATA
from configgen.utils.bezels import createTransparentBezel
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from collections.abc import Mapping
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from _pytest.mark import ParameterSet
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.types import Resolution

_DATA_DIR: Final = Path(__file__).parent.parent.parent.parent / 'data' / 'mame'

with (_DATA_DIR / 'messSystems.csv').open() as _csv:
    _MESS_SYSTEMS = {
        row[0]: {
            'system': row[0],
            'system_name': row[1],
            'rom_type': row[2],
            'autorun': row[3],
        }
        for row in csv.reader(_csv, delimiter=';', quotechar="'")
    }


class _ConfigTest(TypedDict):
    rom: str | list[str]
    model_name: NotRequired[str]
    configs: NotRequired[list[dict[str, str | list[str]]]]


def _make_system_config_params(mapping: Mapping[str, _ConfigTest]) -> tuple[tuple[str, ...], list[ParameterSet]]:
    def _get_params(system: str, test_config: _ConfigTest, /) -> list[ParameterSet]:
        rom_filename = test_config['rom']
        model_name = test_config.get('model_name', system)

        system_params: list[ParameterSet] = []

        def _make_rom_config_param(rom: str, config: dict[str, Any] | None, /) -> ParameterSet:
            return pytest.param(system, rom, model_name, config, id=f'{system}-{rom}-{config}')

        def _make_config_param(config: dict[str, Any] | None, /) -> ParameterSet:
            return pytest.param(system, rom_filename, model_name, config, id=f'{system}-{config}')

        if isinstance(rom_filename, list):
            roms = rom_filename[1:]
            rom_filename = rom_filename[0]
            system_params = [_make_rom_config_param(rom, None) for rom in roms]

        system_params.extend(
            [
                _make_config_param(None),
                _make_config_param({'customcfg': '0'}),
                _make_config_param({'customcfg': '1'}),
                _make_config_param({'pergamecfg': '0'}),
                _make_config_param({'pergamecfg': '1'}),
            ]
        )

        configs = test_config.get('configs')
        if configs:
            for config in configs:
                if len(config) == 1:
                    key, value = next(iter(config.items()))
                    if isinstance(value, list):
                        system_params.extend(_make_config_param({key: v}) for v in value)
                    else:
                        system_params.append(_make_config_param({key: value}))
                else:
                    system_params.append(_make_config_param(config))

        return system_params

    return (
        ('system_name', 'rom', 'model_name', 'mock_system_config'),
        [param for system, test_config in mapping.items() for param in _get_params(system, test_config)],
    )


def _make_control_scheme_params(
    mapping: Mapping[str, list[tuple[str | None, str]]],
) -> tuple[tuple[str, ...], list[ParameterSet]]:
    return (
        ('rom_name', 'mock_system_config', 'control_scheme'),
        [
            pytest.param(rom_name, {} if layout is None else {'altlayout': layout}, scheme, id=f'{rom_name}-{layout}')
            for rom_name, layouts in mapping.items()
            for layout, scheme in layouts
        ],
    )


@pytest.fixture
def system_name() -> str:
    return 'mame'


@pytest.fixture
def emulator() -> str:
    return 'mame'


@pytest.fixture(autouse=True)
def fs(fs: FakeFilesystem) -> FakeFilesystem:
    fs.create_dir('/usr/bin/mame')
    fs.add_real_directory(_DATA_DIR, target_path=DEFAULTS_DIR / 'data' / 'mame')

    return fs


@pytest.fixture
def generator_cls() -> type[MameGenerator]:
    return MameGenerator


@pytest.fixture
def get_bezel_infos(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch('configgen.utils.bezels.getBezelInfos', return_value=getattr(request, 'param', None))


@pytest.fixture
def create_transparent_bezel(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.bezels.createTransparentBezel', return_value=None)


@pytest.fixture
def fast_image_size(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch(
        'configgen.utils.bezels.fast_image_size', return_value=getattr(request, 'param', None) or (0, 0)
    )


@pytest.fixture
def gun_borders_size(mocker: MockerFixture) -> Mock:
    return mocker.patch(
        'configgen.utils.bezels.gunBordersSize', return_value=(mocker.sentinel.inner_size, mocker.sentinel.outer_size)
    )


@pytest.fixture
def gun_border_image(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.bezels.gunBorderImage', return_value=None)


@pytest.fixture
def guns_borders_color_fom_config(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.bezels.gunsBordersColorFomConfig', return_value=mocker.sentinel.borders_color)


@pytest.fixture
def get_mame_machine_size(mocker: MockerFixture, generator_cls: type[MameGenerator], request: SubRequest) -> Mock:
    return mocker.patch.object(
        generator_cls, 'getMameMachineSize', return_value=(0, 0, getattr(request, 'param', None) or 0)
    )


class TestMameGenerator(GeneratorBaseTest):
    @pytest.fixture(autouse=True)
    def guns_borders_size_name(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'tests.mock_emulator.MockEmulator.guns_borders_size_name',
            side_effect=[
                mocker.sentinel.guns_borders_size_name_1,
                mocker.sentinel.guns_borders_size_name_2,
            ],
        )

    @pytest.fixture(autouse=True)
    def guns_border_ratio_type(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'tests.mock_emulator.MockEmulator.guns_border_ratio_type',
            side_effect=[
                mocker.sentinel.guns_border_ratio_type_1,
                mocker.sentinel.guns_border_ratio_type_2,
            ],
        )

    @pytest.fixture(autouse=True)
    def generate_pads_config(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.generators.mame.mameControllers.generatePadsConfig')

    @pytest.fixture(autouse=True)
    def write_bezel_config(self, mocker: MockerFixture, generator_cls: type[MameGenerator]) -> Mock:
        return mocker.patch.object(generator_cls, 'writeBezelConfig')

    @pytest.fixture
    def video_mode_get_screens_infos(self, mocker: MockerFixture, request: SubRequest) -> Mock:
        screen_count = getattr(request, 'param', 1)
        return mocker.patch(
            'configgen.utils.videoMode.getScreensInfos', return_value=[mocker.Mock() for _ in range(screen_count)]
        )

    def test_supports_internal_bezels(self, generator: MameGenerator) -> None:  # pyright: ignore
        assert generator.supportsInternalBezels()

    def test_generate(
        self,
        mocker: MockerFixture,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        write_bezel_config: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mame' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert fs.cwd == '/usr/bin/mame'
        assert not Path('/var/run/mame_software').exists()
        write_bezel_config.assert_called_once_with(
            None,
            mock_system,
            ROMS / 'mame' / 'rom.zip',
            '',
            {'width': 1920, 'height': 1080},
            mocker.sentinel.guns_borders_size_name_1,
            mocker.sentinel.guns_border_ratio_type_1,
        )

    def test_generate_write_bezel_config_fails(
        self,
        mocker: MockerFixture,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        write_bezel_config: Mock,
    ) -> None:
        write_bezel_config.side_effect = [Exception('Test exception'), None]

        generator.generate(
            mock_system,
            ROMS / 'mame' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert fs.cwd == '/usr/bin/mame'
        assert not Path('/var/run/mame_software').exists()
        assert write_bezel_config.call_args_list == [
            mocker.call(
                None,
                mock_system,
                ROMS / 'mame' / 'rom.zip',
                '',
                {'width': 1920, 'height': 1080},
                mocker.sentinel.guns_borders_size_name_1,
                mocker.sentinel.guns_border_ratio_type_1,
            ),
            mocker.call(
                None,
                mock_system,
                ROMS / 'mame' / 'rom.zip',
                '',
                {'width': 1920, 'height': 1080},
                mocker.sentinel.guns_borders_size_name_2,
                mocker.sentinel.guns_border_ratio_type_2,
            ),
        ]

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'video': 'bgfx'},
            {'video': 'bgfx', 'bgfxbackend': 'vulkan'},
            {'video': 'bgfx', 'bgfxshaders': 'crt-geom'},
            {'video': 'accel'},
            {'switchres': '0'},
            {'switchres': '1'},
            {'vsync': '0'},
            {'vsync': '1'},
            {'syncrefresh': '0'},
            {'syncrefresh': '1'},
            {'rotation': 'autoror'},
            {'rotation': 'autorol'},
            {'rotation': 'None'},
            {'artworkcrop': '0'},
            {'artworkcrop': '1'},
            {'customcfg': '0'},
            {'customcfg': '1'},
            {'dataplugin': '0'},
            {'dataplugin': '1'},
            {'offscreenreload': '0'},
            {'offscreenreload': '1'},
            {'hiscoreplugin': '0'},
            {'coindropplugin': '1'},
            {'hiscoreplugin': '1', 'coindropplugin': '1', 'dataplugin': '1'},
            {'multimouse': '1'},
            {'use_guns': '1'},
            {'use_wheels': '1'},
            {'use_mouse': '1'},
            {'use_mouse': '1', 'use_guns': '1'},
            {'bezel': ''},
            {'bezel': 'consoles'},
            {'bezel': 'consoles', 'forceNoBezel': False},
            {'bezel': 'consoles', 'forceNoBezel': True},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: MameGenerator,
        mocker: MockerFixture,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        generate_pads_config: Mock,
        write_bezel_config: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mame' / 'rom.zip',
                mocker.sentinel.players_controllers,  # pyright: ignore
                {},
                mocker.sentinel.guns,  # pyright: ignore
                mocker.sentinel.wheels,  # pyright: ignore
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        config_dir = MAME_CONFIG if mock_system.config.get('customcfg', '0') == '0' else (MAME_CONFIG / 'custom')
        bezel = mock_system.config.get('bezel')
        if not bezel:
            bezel = None
        if mock_system.config.get('forceNoBezel'):
            bezel = None

        assert config_dir.is_dir()
        generate_pads_config.assert_called_once_with(
            config_dir,
            mocker.sentinel.players_controllers,
            '',
            'default',
            mock_system.config.get('customcfg', '0') == '1',
            'none',
            bezel,
            mock_system.config.get('use_guns', '0') == '1',
            mocker.sentinel.guns,
            mock_system.config.get('use_wheels', '0') == '1',
            mocker.sentinel.wheels,
            mock_system.config.get('use_mouse', '0') == '1',
            mock_system.config.get('multimouse', '0') == '1',
            mock_system,
        )

        write_bezel_config.assert_called_once_with(
            bezel,
            mock_system,
            ROMS / 'mame' / 'rom.zip',
            '',
            {'width': 1920, 'height': 1080},
            mocker.sentinel.guns_borders_size_name_1,
            mocker.sentinel.guns_border_ratio_type_1,
        )

    @pytest.mark.parametrize('video_mode_get_screens_infos', [1, 2, 3], indirect=True)
    @pytest.mark.mock_system_config({'multiscreens': '1'})
    @pytest.mark.usefixtures('video_mode_get_screens_infos')
    def test_generate_config_multiscreens(
        self,
        generator: MameGenerator,
        mocker: MockerFixture,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        generate_pads_config: Mock,
        video_mode_get_screens_infos: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mame' / 'rom.zip',
                mocker.sentinel.players_controllers,  # pyright: ignore
                {},
                mocker.sentinel.guns,  # pyright: ignore
                mocker.sentinel.wheels,  # pyright: ignore
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        video_mode_get_screens_infos.assert_called_once_with(mock_system.config)
        generate_pads_config.assert_called_once_with(
            MAME_CONFIG,
            mocker.sentinel.players_controllers,
            '',
            'default',
            mock_system.config.get('customcfg', '0') == '1',
            'none',
            None,
            mock_system.config.get('use_guns', '0') == '1',
            mocker.sentinel.guns,
            False,
            mocker.sentinel.wheels,
            mock_system.config.get('use_mouse', '0') == '1',
            mock_system.config.get('multimouse', '0') == '1',
            mock_system,
        )

    @pytest.mark.parametrize(
        *_make_control_scheme_params(
            {
                'ts2': [  # capcom
                    (None, 'sfsnes'),
                    ('snes', 'sfsnes'),
                    ('megadrive', 'megadrive'),
                    ('fightstick', 'sfstick'),
                    ('neomini', 'neomini'),
                ],
                'mknifty666': [  # mortal kombat
                    (None, 'mksnes'),
                    ('snes', 'mksnes'),
                    ('megadrive', 'mkmegadrive'),
                    ('fightstick', 'mkstick'),
                    ('neomini', 'neomini'),
                ],
                'kinst': [  # killer instinct
                    (None, 'kisnes'),
                    ('snes', 'kisnes'),
                    ('megadrive', 'megadrive'),
                    ('fightstick', 'sfstick'),
                    ('neomini', 'neomini'),
                ],
                '2020bb': [(None, 'neomini'), ('snes', 'neomini')],  # neogeo
                'agentx1': [(None, 'twinstick'), ('snes', 'twinstick')],  # twinstick
                'qbert': [(None, 'qbert'), ('snes', 'qbert')],
                'foobarbaz': [
                    (None, 'default'),
                    ('default', 'default'),
                    ('snes', 'default'),
                    ('megadrive', 'mddefault'),
                    ('fightstick', 'fightstick'),
                    ('neomini', 'neomini'),
                    ('neocd', 'neocd'),
                    ('twinstick', 'twinstick'),
                    ('qbert', 'qbert'),
                ],
            }
        )
    )
    def test_generate_config_control_scheme(
        self,
        generator: MameGenerator,
        rom_name: str,
        control_scheme: str,
        mock_system: Emulator,
        mocker: MockerFixture,
        generate_pads_config: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mame' / f'{rom_name}.zip',
                mocker.sentinel.players_controllers,  # pyright: ignore
                {},
                mocker.sentinel.guns,  # pyright: ignore
                mocker.sentinel.wheels,  # pyright: ignore
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        generate_pads_config.assert_called_once_with(
            MAME_CONFIG,
            mocker.sentinel.players_controllers,
            '',
            control_scheme,
            False,
            'none',
            None,
            False,
            mocker.sentinel.guns,
            False,
            mocker.sentinel.wheels,
            False,
            False,
            mock_system,
        )

    @pytest.mark.parametrize(
        *_make_system_config_params(
            {
                'adam': {
                    'rom': ['rom.bin', 'rom.ddp', 'rom.dsk'],
                    'configs': [
                        {'altromtype': ['cass1', 'cass2', 'flop1', 'flop2', 'cart1', 'cart2', 'cart3', 'cart4']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'advision': {'rom': 'rom.bin'},
                'apfm1000': {'rom': 'rom.bin'},
                'apple2': {
                    'rom': 'rom.nib',
                    'model_name': 'apple2ee',
                    'configs': [
                        {'altromtype': ['cass', 'flop2', 'hard1']},
                        {'gameio': ['none', 'joy', 'joyport', 'gizmo']},
                        {'altmodel': ['apple2e', 'apple2p']},
                        {'altmodel': 'apple2p', 'customcfg': '1'},
                    ],
                },
                'apple2gs': {
                    'rom': 'rom.nib',
                    'configs': [
                        {'altromtype': ['flop2', 'flop3', 'flop4']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'arcadia': {'rom': 'rom.bin'},
                'archimedes': {
                    'rom': 'rom.bin',
                    'model_name': 'aa4401',
                    'configs': [
                        {'altmodel': ['aa310', 'aa3000', 'aa540']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'astrocde': {'rom': 'rom.bin'},
                'atom': {
                    'rom': 'rom.bin',
                    'configs': [
                        {'altromtype': ['cass', 'flop2', 'cart', 'quik']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'bbc': {
                    'rom': 'rom.bin',
                    'model_name': 'bbcb',
                    'configs': [
                        {'sticktype': ['none', 'acornjoy']},
                        {'altromtype': ['cass', 'rom1', 'rom2', 'rom3', 'rom4', 'flop2', 'cart1', 'cart2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'camplynx': {
                    'rom': 'rom.bin',
                    'model_name': 'lynx48k',
                    'configs': [
                        {'altmodel': ['lynx96k', 'lynx128k']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'cdi': {
                    'rom': 'rom.bin',
                    'model_name': 'cdimono1',
                },
                'coco': {
                    'rom': ['rom.rom', 'rom.cas', 'rom.dsk'],
                    'model_name': 'coco3',
                    'configs': [
                        {'altmodel': ['coco', 'coco2', 'coco2b', 'coco3p']},
                        {'altromtype': ['cass', 'flop1']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'crvision': {
                    'rom': 'rom.rom',
                    'configs': [
                        {'altromtype': 'cass'},
                    ],
                },
                'electron': {
                    'rom': 'rom.rom',
                    'model_name': 'electron64',
                    'configs': [
                        {'altmodel': 'electron'},
                        {'altromtype': ['flop', 'cart1', 'cart2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'fm7': {
                    'rom': 'rom.rom',
                    'configs': [
                        {'altmodel': 'fm77av'},
                        {'altromtype': ['cass', 'flop2']},
                        # TODO: this setting doesn't do anything because the generator
                        # checks this setting for a bool and these values are treated
                        # as False
                        {'addblankdisk': ['cass', 'flop1', 'flop2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'fmtowns': {
                    'rom': 'rom.bin',
                    'model_name': 'fmtmarty',
                    'configs': [
                        {'altmodel': ['fmtowns', 'fmtownsux']},
                        {'ramsize': ['2', '4']},
                        {'altromtype': ['flop1', 'flop2', 'hard1']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'gamate': {'rom': 'rom.bin'},
                'gameandwatch': {'rom': 'rom.mgw', 'model_name': ''},
                'gamecom': {'rom': 'rom.bin'},
                'gamepock': {'rom': 'rom.bin'},
                'gmaster': {'rom': 'rom.bin'},
                'gp32': {'rom': 'rom.smc'},
                'laser310': {
                    'rom': 'rom.vz',
                    'configs': [
                        {'memslot': 'laser310_16k'},
                        {'altromtype': ['cass', 'snap']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'lcdgames': {'rom': 'rom.mgw', 'model_name': ''},
                'macintosh': {
                    'rom': 'rom.dsk',
                    'model_name': 'maclc3',
                    'configs': [
                        {'altmodel': ['mac128k', 'mac512k', 'macplus', 'macse', 'macclasc', 'mac2dhd', 'maciix']},
                        {'ramsize': '2'},
                        {'ramsize': '96'},
                        {'ramsize': '16', 'altmodel': 'maciix'},
                        {'ramsize': '48', 'altmodel': 'maciix'},
                        {'ramsize': '48', 'altmodel': 'maciix', 'imagereader': 'disabled'},
                        {'ramsize': '48', 'altmodel': 'maciix', 'imagereader': 'nbb'},
                        {'ramsize': '48', 'altmodel': 'maciix', 'imagereader': 'nbc'},
                        {'ramsize': '48', 'altmodel': 'maciix', 'imagereader': 'nbd'},
                        {'ramsize': '48', 'altmodel': 'maciix', 'imagereader': 'nbe'},
                        {'ramsize': '96', 'altmodel': 'macplus'},
                        {'altromtype': ['cdrm', 'hard']},
                        {'bootdisk': ['macos3', 'macos608', 'macos701', 'macos75', 'mac608', 'mac701', 'mac755']},
                        {'bootdisk': 'macos30', 'altromtype': 'cdrm'},
                        {'enableui': ['0', '1']},
                    ],
                },
                'megaduck': {'rom': 'rom.bin'},
                'neogeo': {
                    'rom': 'rom.zip',
                    'model_name': '',
                    'configs': [
                        {'hiscoreplugin': '0'},
                        {'coindropplugin': '1'},
                        {'hiscoreplugin': '1', 'coindropplugin': '1', 'dataplugin': '1'},
                    ],
                },
                'pdp1': {
                    'rom': 'rom.tap',
                    'configs': [
                        {'enableui': ['0', '1']},
                    ],
                },
                'plugnplay': {'rom': 'rom.zip', 'model_name': ''},
                'pv1000': {'rom': 'rom.bin'},
                'socrates': {
                    'rom': 'rom.tap',
                    'configs': [
                        {'enableui': ['0', '1']},
                    ],
                },
                'supracan': {'rom': 'rom.bin'},
                'ti99': {
                    'rom': 'rom.bin',
                    'model_name': 'ti99_4a',
                    'configs': [
                        {'ti99_32kram': '0'},
                        {'ti99_32kram': '1'},
                        {'ti99_speech': '0'},
                        {'altromtype': ['cass1', 'cass2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'tutor': {
                    'rom': 'rom.bin',
                    'configs': [
                        {'altromtype': 'cass'},
                        {'enableui': ['0', '1']},
                    ],
                },
                'vectrex': {'rom': 'rom.gam'},
                'vgmplay': {'rom': 'rom.vgm'},
                'vsmile': {'rom': 'rom.u1'},
                'xegs': {
                    'rom': 'rom.atr',
                    'configs': [
                        {'altromtype': ['flop1', 'flop2', 'flop3', 'flop4']},
                        {'enableui': ['0', '1']},
                    ],
                },
            }
        )
    )
    def test_generate_system_config(
        self,
        mocker: MockerFixture,
        generator: MameGenerator,
        mock_system: Emulator,
        rom: str,
        model_name: str,
        write_bezel_config: Mock,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / rom,
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (
            MAME_CONFIG / model_name
            if mock_system.config.get('customcfg', '0') == '0'
            else (MAME_CONFIG / model_name / 'custom')
        ).is_dir()
        if mock_system.config.get('pergamecfg', '0') == '1' and model_name:
            assert (MAME_CONFIG / model_name / rom).is_dir()
        else:
            assert not (MAME_CONFIG / model_name / rom).exists()

        write_bezel_config.assert_called_once_with(
            None,
            mock_system,
            ROMS / mock_system.name / rom,
            _MESS_SYSTEMS.get(mock_system.name, {'system_name': ''})['system_name'],
            {'width': 1920, 'height': 1080},
            mocker.sentinel.guns_borders_size_name_1,
            mocker.sentinel.guns_border_ratio_type_1,
        )

    @pytest.mark.system_name('adam')
    @pytest.mark.mock_system_config({'softList': 'adam_cart'})
    def test_generate_adam_softlist(
        self,
        generator: MameGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'adam' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/var/run/mame_software/hash').is_dir()
        assert Path('/var/run/mame_software/hash/adam_cart.xml').is_symlink()
        assert Path('/var/run/mame_software/hash/adam_cart.xml').resolve() == Path('/usr/bin/mame/hash/adam_cart.xml')
        assert Path('/var/run/mame_software/adam_cart').resolve() == Path('/userdata/roms/adam')

    @pytest.mark.system_name('adam')
    @pytest.mark.mock_system_config({'softList': 'adam_cart'})
    def test_generate_adam_softlist_existing_files(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/var/run/mame_software/hash')
        fs.create_file('/usr/bin/mame/hash/arcadia.xml')
        fs.create_dir('/userdata/roms/arcadia')
        fs.create_symlink('/var/run/mame_software/hash/arcadia.xml', '/usr/bin/mame/hash/arcadia.xml')
        fs.create_symlink('/var/run/mame_software/arcadia', '/userdata/roms/arcadia')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'adam' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/var/run/mame_software/hash').is_dir()
        assert Path('/var/run/mame_software/hash/adam_cart.xml').is_symlink()
        assert Path('/var/run/mame_software/hash/adam_cart.xml').resolve() == Path('/usr/bin/mame/hash/adam_cart.xml')
        assert Path('/var/run/mame_software/adam_cart').resolve() == Path('/userdata/roms/adam')
        assert not Path('/var/run/mame_software/hash/arcadia.xml').exists()
        assert not Path('/var/run/mame_software/arcadia').exists()

    @pytest.mark.parametrize(
        ('system_name', 'mock_system_config'),
        [
            pytest.param('macintosh', {'softList': 'mac_hdd'}, id='mac_hdd'),
            pytest.param('bbc', {'softList': 'bbc_hdd'}, id='bbc_hdd'),
            pytest.param('cdi', {'softList': 'cdi'}, id='cdi'),
            pytest.param('archimedes', {'softList': 'archimedes_hdd'}, id='archimedes_hdd'),
            pytest.param('fmtowns', {'softList': 'fmtowns_cd'}, id='fmtowns_cd'),
        ],
    )
    def test_generate_softlist_dir(
        self,
        generator: MameGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'mame' / 'some' / 'subdir' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        softlist = mock_system.config['softList']

        assert Path('/var/run/mame_software/hash').is_dir()
        assert Path(f'/var/run/mame_software/hash/{softlist}.xml').is_symlink()
        assert Path(f'/var/run/mame_software/hash/{softlist}.xml').resolve() == Path(
            f'/usr/bin/mame/hash/{softlist}.xml'
        )
        assert Path(f'/var/run/mame_software/{softlist}').is_symlink()
        assert Path(f'/var/run/mame_software/{softlist}').resolve() == Path('/userdata/roms/mame/some')

    @pytest.mark.system_name('bbc')
    @pytest.mark.parametrize('mock_system_config', [{'softList': 'bbc_cass'}, {'softList': 'bbcb_flop'}])
    def test_generate_bbc_softlist(
        self,
        generator: MameGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'bbc' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('fm7')
    @pytest.mark.parametrize('mock_system_config', [{'softList': 'fm77av'}, {'softList': 'fm7_cass'}])
    def test_generate_fm7_softlist(
        self,
        generator: MameGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'fm7' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.parametrize(
        ('mock_system_config', 'rom_extension'),
        [
            ({'softList': 'coco_cass'}, 'zip'),
            ({'softList': 'coco_cass'}, 'BAS.zip'),
            ({'softList': 'coco_flop'}, 'zip'),
            ({'softList': 'coco_flop'}, 'BAS.zip'),
        ],
    )
    def test_generate_coco_autorun(
        self,
        generator: MameGenerator,
        mock_system: Emulator,
        rom_extension: str,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'coco' / f'rom.{rom_extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_flop'})
    def test_generate_coco_autorun_xml(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/bin/mame/hash/coco_flop.xml',
            contents="""<?xml version="1.0"?>
<!DOCTYPE softwarelist SYSTEM "softwarelist.dtd">
<softwarelist name="coco_flop" description="Tandy Radio Shack Color Computer disk images">
	<software name="zonx">
		<description>Zonx (The Rainbow)</description>
		<year>1985</year>
		<publisher>Falsoft</publisher>
		<info name="author" value="David Billen" />
		<info name="usage" value="LOADM&quot;ZONX&quot;:EXEC" />
		<sharedfeat name="compatibility" value="COCO,COCO3" />
		<part name="flop0" interface="floppy_5_25">
			<dataarea name="flop" size="161280">
				<rom name="ZONX.DSK" size="161280" crc="da6a8b6c" sha1="fdd3ef04a6e2fcc854a467ae735f2af43c838af2" />
			</dataarea>
		</part>
	</software>
</softwarelist>
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'coco' / 'zonx.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_flop'})
    def test_generate_coco_autorun_xml_no_entry(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            '/usr/bin/mame/hash/coco_flop.xml',
            contents="""<?xml version="1.0"?>
<!DOCTYPE softwarelist SYSTEM "softwarelist.dtd">
<softwarelist name="coco_flop" description="Tandy Radio Shack Color Computer disk images">
	<software name="zonx">
	</software>
</softwarelist>
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'coco' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_cart'})
    def test_generate_coco_autoload_csv(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            MAME_CONFIG / 'autoload' / 'coco_cart_autoload.csv',
            contents="""# A comment
RoM;\\n*RUN\\n*THIS\\n*STUFF
foo;\\n*RUN\\n*OTHER\\n*STUFF
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'coco' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('fmtowns')
    @pytest.mark.mock_system_config({'addblankdisk': '1'})
    @pytest.mark.parametrize('existing', [False, True])
    @pytest.mark.parametrize('altromtype', [None, 'flop1', 'flop2', 'cdrm', 'hard1'])
    @pytest.mark.parametrize('altmodel', [None, 'fmtowns', 'fmtownsux'])
    def test_generate_fmtowns_addblankdisk(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        altmodel: str | None,
        altromtype: str | None,
        existing: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/share/mame/blank.fmtowns', contents='blank')

        if existing:
            fs.create_file('/userdata/saves/mame/fmtowns/rom', contents='existing blank')

        if altmodel:
            mock_system.config['altmodel'] = altmodel

        if altromtype:
            mock_system.config['altromtype'] = altromtype

        assert (
            generator.generate(
                mock_system,
                ROMS / 'fmtowns' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert Path('/userdata/saves/mame/fmtowns/rom').read_text() == ('existing blank' if existing else 'blank')

    @pytest.mark.system_name('electron')
    @pytest.mark.mock_system_config({'softList': 'electron_flop'})
    def test_generate_autoload_csv_generic(
        self,
        generator: MameGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            MAME_DEFAULT_DATA / 'electron_flop_autoload.csv',
            contents="""# A comment
RoM;\\n*RUN\\n*THIS\\n*STUFF
foo;\\n*RUN\\n*OTHER\\n*STUFF
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'electron' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )


@pytest.mark.parametrize('borders_size', [None, 'medium'])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
def test_write_bezel_config(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    mame_system: str,
    get_bezel_infos: Mock,
    borders_size: str | None,
    gun_borders_size: Mock,
    guns_borders_color_fom_config: Mock,
    gun_border_image: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    fs.create_file(
        '/path/to/mame.info',
        contents=json.dumps(
            {
                'width': 1920,
                'height': 1080,
                'top': 24,
                'left': 273,
                'bottom': 24,
                'right': 273,
                'opacity': 1.0000000,
                'messagex': 0.220000,
                'messagey': 0.120000,
            },
            indent=2,
        ),
    )
    fs.create_file('/path/to/mame.png')

    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    get_bezel_infos.return_value = {
        'layout': Path('/path/to/mame.lay'),
        'png': Path('/path/to/mame.png'),
        'info': Path('/path/to/mame.info'),
    }

    generator_cls.writeBezelConfig(
        'consoles',
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        mame_system,
        {'width': 1920, 'height': 1080},
        borders_size,
        None,
    )

    get_bezel_infos.assert_called_once_with(ROMS / 'system' / 'rom name.zip', 'consoles', mock_system.name, 'mame')

    assert (expected_dir / 'default.lay').read_text() == snapshot

    if borders_size:
        gun_borders_size.assert_called_once_with(borders_size)
        guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
        gun_border_image.assert_called_once_with(
            expected_dir / 'default.png',
            Path('/tmp/bezel_gunborders.png'),
            None,
            mocker.sentinel.inner_size,
            mocker.sentinel.outer_size,
            mocker.sentinel.borders_color,
        )
        assert (expected_dir / 'default.png').resolve() == Path('/tmp/bezel_gunborders.png')
    else:
        gun_borders_size.assert_not_called()
        guns_borders_color_fom_config.assert_not_called()
        gun_border_image.assert_not_called()

        assert (expected_dir / 'default.png').resolve() == Path('/path/to/mame.png')


@pytest.mark.parametrize('borders_size', [None, 'medium'])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
@pytest.mark.usefixtures('gun_borders_size', 'guns_borders_color_fom_config', 'gun_border_image')
def test_write_bezel_config_existing(
    fs: FakeFilesystem,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    mame_system: str,
    get_bezel_infos: Mock,
    borders_size: str | None,
) -> None:
    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')
    fs.create_file(expected_dir / 'foo.txt')

    fs.create_file(
        '/path/to/mame.info',
        contents=json.dumps(
            {
                'width': 1920,
                'height': 1080,
                'top': 24,
                'left': 273,
                'bottom': 24,
                'right': 273,
                'opacity': 1.0000000,
                'messagex': 0.220000,
                'messagey': 0.120000,
            },
            indent=2,
        ),
    )
    fs.create_file('/path/to/mame.png')

    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    get_bezel_infos.return_value = {
        'layout': Path('/path/to/mame.lay'),
        'png': Path('/path/to/mame.png'),
        'info': Path('/path/to/mame.info'),
    }

    generator_cls.writeBezelConfig(
        'consoles',
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        mame_system,
        {'width': 1920, 'height': 1080},
        borders_size,
        None,
    )

    assert not (expected_dir / 'foo.txt').exists()


@pytest.mark.parametrize('borders_size', [None, 'medium'])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
def test_write_bezel_config_layout(
    mocker: MockerFixture,
    fs: FakeFilesystem,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    mame_system: str,
    get_bezel_infos: Mock,
    borders_size: str | None,
    gun_borders_size: Mock,
    guns_borders_color_fom_config: Mock,
    gun_border_image: Mock,
) -> None:
    fs.create_file('/path/to/mame.lay')
    fs.create_file('/path/to/mame.png')
    get_bezel_infos.return_value = {'layout': Path('/path/to/mame.lay'), 'png': Path('/path/to/mame.png')}

    generator_cls.writeBezelConfig(
        'consoles',
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        mame_system,
        {'width': 1920, 'height': 1080},
        borders_size,
        None,
    )

    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    assert (expected_dir / 'default.lay').resolve() == Path('/path/to/mame.lay')
    get_bezel_infos.assert_called_once_with(ROMS / 'system' / 'rom name.zip', 'consoles', mock_system.name, 'mame')

    if borders_size:
        gun_borders_size.assert_called_once_with(borders_size)
        guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
        gun_border_image.assert_called_once_with(
            expected_dir / 'mame.png',
            Path('/tmp/bezel_gunborders.png'),
            None,
            mocker.sentinel.inner_size,
            mocker.sentinel.outer_size,
            mocker.sentinel.borders_color,
        )
        assert (expected_dir / 'mame.png').resolve() == Path('/tmp/bezel_gunborders.png')
    else:
        gun_borders_size.assert_not_called()
        guns_borders_color_fom_config.assert_not_called()
        gun_border_image.assert_not_called()

        assert (expected_dir / 'mame.png').resolve() == Path('/path/to/mame.png')


@pytest.mark.parametrize('get_mame_machine_size', [0, 90, 270], indirect=True)
@pytest.mark.parametrize('resolution', [{'width': 1920, 'height': 1080}, {'width': 1920, 'height': 1201}], ids=str)
@pytest.mark.parametrize('bezel', [None, 'consoles'])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
@pytest.mark.usefixtures('get_bezel_infos')
def test_write_bezel_config_transparent(
    mocker: MockerFixture,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    bezel: str | None,
    mame_system: str,
    resolution: Resolution,
    create_transparent_bezel: Mock,
    fast_image_size: Mock,
    get_mame_machine_size: Mock,
    gun_borders_size: Mock,
    gun_border_image: Mock,
    guns_borders_color_fom_config: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    fast_image_size.return_value = (resolution['width'], resolution['height'])

    generator_cls.writeBezelConfig(
        bezel,
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        mame_system,
        resolution,
        'medium',
        None,
    )
    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    create_transparent_bezel.assert_called_once_with(
        Path('/tmp/bezel_transmame_black.png'), resolution['width'], resolution['height']
    )
    fast_image_size.assert_called_once_with(Path('/tmp/bezel_transmame_black.png'))
    get_mame_machine_size.assert_called_once_with(
        'rom name', Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')
    )
    gun_borders_size.assert_called_once_with('medium')
    guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
    gun_border_image.assert_called_once_with(
        Path(f'/var/run/mame_artwork/{mame_system or "rom name"}/default.png'),
        Path('/tmp/bezel_gunborders.png'),
        None,
        mocker.sentinel.inner_size,
        mocker.sentinel.outer_size,
        mocker.sentinel.borders_color,
    )
    assert Path(expected_dir / 'default.png').resolve() == Path('/tmp/bezel_gunborders.png')
    assert (expected_dir / 'default.lay').read_text() == snapshot


@pytest.mark.parametrize('resolution', [{'width': 1920, 'height': 1080}, {'width': 1920, 'height': 1201}], ids=str)
@pytest.mark.parametrize('bezel', [None, 'consoles'])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
@pytest.mark.usefixtures('get_bezel_infos')
def test_write_bezel_config_transparent_raises(
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    bezel: str | None,
    mame_system: str,
    resolution: Resolution,
    create_transparent_bezel: Mock,
    fast_image_size: Mock,
    get_mame_machine_size: Mock,
    gun_borders_size: Mock,
    gun_border_image: Mock,
    guns_borders_color_fom_config: Mock,
) -> None:
    get_mame_machine_size.side_effect = Exception('Test exception')
    fast_image_size.return_value = (resolution['width'], resolution['height'])

    with pytest.raises(Exception, match=r'^Test exception$'):
        generator_cls.writeBezelConfig(
            bezel,
            mock_system,
            ROMS / 'system' / 'rom name.zip',
            mame_system,
            resolution,
            'medium',
            None,
        )

    create_transparent_bezel.assert_called_once_with(
        Path('/tmp/bezel_transmame_black.png'), resolution['width'], resolution['height']
    )
    fast_image_size.assert_called_once_with(Path('/tmp/bezel_transmame_black.png'))
    get_mame_machine_size.assert_called_once_with(
        'rom name', Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')
    )
    gun_borders_size.assert_not_called()
    guns_borders_color_fom_config.assert_not_called()
    gun_border_image.assert_not_called()


@pytest.mark.parametrize('existing', [True, False])
@pytest.mark.parametrize('mame_system', ['', 'adam'])
def test_write_bezel_config_mamezip(
    fs: FakeFilesystem,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    mame_system: str,
    get_bezel_infos: Mock,
    existing: bool,
) -> None:
    if existing:
        fs.create_file(f'/var/run/mame_artwork/{mame_system or "rom name"}.zip')

    fs.create_file('/path/to/mame.zip')
    get_bezel_infos.return_value = {'mamezip': Path('/path/to/mame.zip')}

    generator_cls.writeBezelConfig(
        'consoles',
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        mame_system,
        {'width': 1920, 'height': 1200},
        None,
        None,
    )

    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    assert not len(list(expected_dir.iterdir()))
    assert Path(f'/var/run/mame_artwork/{mame_system or "rom name"}.zip').resolve() == Path('/path/to/mame.zip')
    get_bezel_infos.assert_called_once_with(ROMS / 'system' / 'rom name.zip', 'consoles', mock_system.name, 'mame')


@pytest.mark.parametrize('corner', [None, 'NW', 'NE', 'SE', 'SW'])
@pytest.mark.parametrize(
    ('bezel_tattoo', 'system_name', 'tattoo_file'),
    [
        ('system', 'adam', None),
        ('system', 'mame', None),
        ('custom', 'adam', 'missing'),
        ('custom', 'adam', 'snes'),
    ],
    ids=str,
)
def test_write_bezel_config_tattoo(
    fs: FakeFilesystem,
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    bezel_tattoo: str | None,
    tattoo_file: str | None,
    corner: str | None,
    get_bezel_infos: Mock,
    snapshot: SnapshotAssertion,
) -> None:
    fs.add_real_directory(
        Path(__file__).parent.parent / 'utils' / '__files__' / 'controller-overlays',
        target_path='/usr/share/batocera/controller-overlays',
    )
    fs.create_file(
        '/path/to/mame.info',
        contents=json.dumps(
            {
                'width': 1920,
                'height': 1080,
                'top': 24,
                'left': 273,
                'bottom': 24,
                'right': 273,
                'opacity': 1.0000000,
                'messagex': 0.220000,
                'messagey': 0.120000,
            },
            indent=2,
        ),
    )
    createTransparentBezel(Path('/path/to/mame.png'), 1920, 1080)
    get_bezel_infos.return_value = {'info': Path('/path/to/mame.info'), 'png': Path('/path/to/mame.png')}

    mock_system.config['bezel.tattoo'] = bezel_tattoo

    if tattoo_file:
        mock_system.config['bezel.tattoo_file'] = (
            f'/tmp/{tattoo_file}.png'
            if tattoo_file == 'missing'
            else f'/usr/share/batocera/controller-overlays/{tattoo_file}.png'
        )

    if corner:
        mock_system.config['bezel.tattoo_corner'] = corner

    generator_cls.writeBezelConfig(
        'consoles',
        mock_system,
        ROMS / 'system' / 'rom name.zip',
        '' if mock_system.name == 'mame' else mock_system.name,
        {'width': 1920, 'height': 1080},
        None,
        None,
    )

    expected_dir = Path(f'/var/run/mame_artwork/{"rom name" if mock_system.name == "mame" else mock_system.name}')

    assert (expected_dir / 'default.png').resolve() == Path('/tmp/bezel_tattooed.png')
    assert Path('/tmp/bezel_tattooed.png').read_bytes() == snapshot(extension_class=PNGImageSnapshotExtension)


@pytest.mark.parametrize(
    ('bezel', 'guns_borders_size', 'resolution'),
    [
        (None, None, {'width': 1920, 'height': 1200}),
        ('consoles', None, {'width': 1920, 'height': 1201}),
        ('consoles', None, {'width': 1920, 'height': 1200}),
    ],
    ids=str,
)
@pytest.mark.parametrize('mame_system', ['', 'adam'])
@pytest.mark.usefixtures('get_bezel_infos')
def test_write_bezel_config_no_write(
    mock_system: Emulator,
    generator_cls: type[MameGenerator],
    bezel: str | None,
    guns_borders_size: str | None,
    resolution: Resolution,
    mame_system: str,
) -> None:
    generator_cls.writeBezelConfig(
        bezel, mock_system, ROMS / 'system' / 'rom name.zip', mame_system, resolution, guns_borders_size, None
    )

    expected_dir = Path(f'/var/run/mame_artwork/{mame_system or "rom name"}')

    assert not expected_dir.exists() or not len(list(expected_dir.iterdir()))


def test_get_mame_machine_size(
    mocker: MockerFixture, fs: FakeFilesystem, subprocess_popen: Mock, generator_cls: type[MameGenerator]
) -> None:
    mock_popen = mocker.Mock()
    mock_popen.communicate.return_value = (
        b"""<mame>
    <machine>
        <display width="256" height="224" rotate="270" />
    </machine>
</mame>
""",
        b'',
    )
    mock_popen.returncode = 0

    subprocess_popen.return_value = mock_popen

    fs.create_dir('/tmp/dir')

    assert generator_cls.getMameMachineSize('machine', Path('/tmp/dir')) == (256, 224, 270)


def test_get_mame_machine_size_listxml_fails(
    mocker: MockerFixture, subprocess_popen: Mock, generator_cls: type[MameGenerator]
) -> None:
    mock_popen = mocker.Mock()
    mock_popen.communicate.return_value = (
        b'',
        b'',
    )
    mock_popen.returncode = 1

    subprocess_popen.return_value = mock_popen

    with pytest.raises(BatoceraException, match='mame -listxml machine failed'):
        generator_cls.getMameMachineSize('machine', Path('/tmp/dir'))


def test_get_mame_machine_size_no_display_elements(
    mocker: MockerFixture, fs: FakeFilesystem, subprocess_popen: Mock, generator_cls: type[MameGenerator]
) -> None:
    mock_popen = mocker.Mock()
    mock_popen.communicate.return_value = (
        b"""<mame>
    <machine />
</mame>
""",
        b'',
    )
    mock_popen.returncode = 0

    subprocess_popen.return_value = mock_popen

    fs.create_dir('/tmp/dir')

    with pytest.raises(BatoceraException, match='Display element not found'):
        generator_cls.getMameMachineSize('machine', Path('/tmp/dir'))


@pytest.mark.parametrize(
    ('system_name', 'model_name', 'special_controller', 'decorations'),
    [
        ('mame', '', 'none', 'consoles'),
        ('adam', 'adam', 'none', 'consoles'),
        ('advision', 'advision', 'none', 'consoles'),
        ('apfm1000', 'apfm1000', 'none', 'consoles'),
        *(
            ('apple2', model_name, gameio, 'consoles')
            for model_name in ['apple2p', 'apple2e', 'apple2ee']
            for gameio in ['none', 'joy', 'joyport', 'gizmo']
        ),
        ('apple2gs', 'apple2gs', 'none', 'consoles'),
        ('arcadia', 'arcadia', 'none', 'consoles'),
        *(('archimedes', model_name, 'none', 'consoles') for model_name in ['aa310', 'aa3000', 'aa4401', 'aa540']),
        ('astrocde', 'astrocde', 'none', 'consoles'),
        ('atom', 'atom', 'none', 'consoles'),
        *(
            ('bbc', 'bbcb', sticktype, 'consoles')
            for sticktype in ['none', 'acornjoy', 'bitstik1', 'bitstik2', 'voltmace3b']
        ),
        *(('camplynx', model_name, 'none', 'consoles') for model_name in ['lynx48k', 'lynx96k', 'lynx128k']),
        *(('cdi', 'cdimono1', 'none', decorations) for decorations in ['consoles', 'none']),
        *(('coco', model_name, 'none', 'consoles') for model_name in ['coco', 'coco2', 'coco2b', 'coco3', 'coco3p']),
        ('crvision', 'crvision', 'none', 'consoles'),
        *(('electron', model_name, 'none', 'consoles') for model_name in ['electron', 'electron64']),
        *(('fm7', model_name, 'none', 'consoles') for model_name in ['fm7', 'fm77av']),
        *(('fmtowns', model_name, 'none', 'consoles') for model_name in ['fmtmarty', 'fmtowns', 'fmtownsux']),
        ('gamate', 'gamate', 'none', 'consoles'),
        ('gameandwatch', '', 'none', 'consoles'),
        ('gamecon', 'gamecon', 'none', 'consoles'),
        ('gamepock', 'gamepock', 'none', 'consoles'),
        ('gmaster', 'gmaster', 'none', 'consoles'),
        ('gp32', 'gp32', 'none', 'consoles'),
        ('laser310', 'laser310', 'none', 'consoles'),
        ('lcdgames', '', 'none', 'consoles'),
        *(
            ('macintosh', model_name, 'none', 'consoles')
            for model_name in ['mac128k', 'mac512k', 'macplus', 'macse', 'macclasc', 'mac2fdhd', 'maciix', 'maclc3']
        ),
        ('megaduck', 'megaduck', 'none', 'consoles'),
        ('neogeo', '', 'none', 'consoles'),
        ('pdp1', 'pdp1', 'none', 'consoles'),
        ('plugnplay', '', 'none', 'consoles'),
        ('pv1000', 'pv1000', 'none', 'consoles'),
        ('socrates', 'socrates', 'none', 'consoles'),
        ('supracan', 'supracan', 'none', 'consoles'),
        ('ti99', 'ti99_4a', 'none', 'consoles'),
        ('tutor', 'tutor', 'none', 'consoles'),
        ('vc4000', 'vc4000', 'none', 'consoles'),
        ('vectrex', 'vectrex', 'none', 'consoles'),
        ('vgmplay', 'vgmplay', 'none', 'consoles'),
        ('vsmile', 'vsmile', 'none', 'consoles'),
        ('xegs', 'xegs', 'none', 'consoles'),
    ],
)
def test_generate_pads_config(
    fs: FakeFilesystem,
    mock_system: Emulator,
    model_name: str,
    special_controller: str,
    decorations: str,
    generic_xbox_pad: Controller,
    ps3_controller: Controller,
    gpio_controller_1: Controller,
    snapshot: SnapshotAssertion,
) -> None:
    fs.create_dir(MAME_CONFIG)

    generatePadsConfig(
        MAME_CONFIG,
        make_player_controller_list(generic_xbox_pad, ps3_controller, gpio_controller_1),
        model_name,
        'default',
        False,
        special_controller,
        decorations,
        False,
        [],
        False,
        {},
        False,
        False,
        mock_system,
    )

    assert (MAME_CONFIG / 'default.cfg').read_text() == snapshot
    if model_name in [
        'cdimono1',
        'apfm1000',
        'astrocde',
        'adam',
        'arcadia',
        'gamecom',
        'tutor',
        'crvision',
        'bbcb',
        'bbcm',
        'bbcm512',
        'bbcmc',
        'xegs',
        'socrates',
        'vgmplay',
        'pdp1',
        'vc4000',
        'fmtmarty',
        'gp32',
        'apple2p',
        'apple2e',
        'apple2ee',
    ]:
        assert (MAME_CONFIG / f'{model_name}.cfg').read_text() == snapshot(name='system-config')
    else:
        assert not (MAME_CONFIG / f'{model_name}.cfg').exists()
