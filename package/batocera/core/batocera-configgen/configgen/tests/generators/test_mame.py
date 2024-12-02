from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, NotRequired, TypedDict

import pytest

from configgen.batoceraPaths import DEFAULTS_DIR
from configgen.generators.mame.mameControllers import generatePadsConfig
from configgen.generators.mame.mamePaths import MAME_CONFIG, MAME_DEFAULT_DATA
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from collections.abc import Mapping
    from unittest.mock import Mock

    from _pytest.mark import ParameterSet
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


_DATA_DIR: Final = Path(__file__).parent.parent.parent.parent / 'data' / 'mame'


class _ConfigTest(TypedDict):
    rom: str | list[str]
    rom_dir: NotRequired[str]
    customcfg_dir: NotRequired[str]
    pergamecfg_dir: NotRequired[str]
    configs: NotRequired[list[dict[str, str | list[str]]]]


def _make_system_config_params(mapping: Mapping[str, _ConfigTest]) -> tuple[tuple[str, ...], list[ParameterSet]]:
    def _get_params(system: str, test_config: _ConfigTest, /) -> list[ParameterSet]:
        rom_filename = test_config['rom']
        rom_dir = test_config.get('rom_dir', system)
        pergamecfg_dir = test_config.get('pergamecfg_dir', system)
        customcfg_dir = test_config.get('customcfg_dir', system)

        system_params: list[ParameterSet] = []

        def _make_rom_config_param(rom: str, config: dict[str, Any] | None, /) -> ParameterSet:
            return pytest.param(
                system, rom_dir, rom, pergamecfg_dir, customcfg_dir, config, id=f'{system}-{rom}-{config}'
            )

        def _make_config_param(config: dict[str, Any] | None, /) -> ParameterSet:
            return pytest.param(
                system, rom_dir, rom_filename, pergamecfg_dir, customcfg_dir, config, id=f'{system}-{config}'
            )

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
        ('system_name', 'rom_dir', 'rom', 'pergamecfg_dir', 'customcfg_dir', 'mock_system_config'),
        [param for system, test_config in mapping.items() for param in _get_params(system, test_config)],
    )


def _make_altlayout_params(mapping: Mapping[str, list[tuple[str, str]]]) -> tuple[tuple[str, ...], list[ParameterSet]]:
    return (
        ('rom_name', 'mock_system_config', 'control_scheme'),
        [
            pytest.param(rom_name, {'altlayout': layout}, scheme, id=f'{rom_name}-{layout}')
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


class TestMameGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        from configgen.generators.mame.mameGenerator import MameGenerator

        return MameGenerator

    @pytest.fixture(autouse=True)
    def guns_borders_size_name(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.controllersConfig.gunsBordersSizeName', return_value=None)

    @pytest.fixture(autouse=True)
    def guns_border_ratio_type(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.controllersConfig.gunsBorderRatioType', return_value=None)

    @pytest.fixture(autouse=True)
    def generate_pads_config(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.generators.mame.mameControllers.generatePadsConfig')

    def test_supports_internal_bezels(self, generator: Generator) -> None:
        assert generator.supportsInternalBezels()

    def test_generate(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/mame/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert fs.cwd == '/usr/bin/mame'
        assert not Path('/var/run/mame_software').exists()

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
            {'rotation': None},
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
            {'use_mouse': '1'},
            {'use_mouse': '1', 'use_guns': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Generator,
        mocker: MockerFixture,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        generate_pads_config: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/mame/rom.zip',
                one_player_controllers,
                {},
                mocker.sentinel.guns,  # pyright: ignore
                mocker.sentinel.wheels,  # pyright: ignore
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        config_dir = MAME_CONFIG if mock_system.config.get('customcfg', '0') == '0' else (MAME_CONFIG / 'custom')

        assert config_dir.is_dir()
        generate_pads_config.assert_called_once_with(
            config_dir,
            one_player_controllers,
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
        *_make_altlayout_params(
            {
                'ts2': [  # capcom
                    ('snes', 'sfsnes'),
                    ('megadrive', 'megadrive'),
                    ('fightstick', 'sfstick'),
                    ('neomini', 'neomini'),
                ],
                'mknifty666': [  # mortal kombat
                    ('snes', 'mksnes'),
                    ('megadrive', 'mkmegadrive'),
                    ('fightstick', 'mkstick'),
                    ('neomini', 'neomini'),
                ],
                'kinst': [  # killer instinct
                    ('snes', 'kisnes'),
                    ('megadrive', 'megadrive'),
                    ('fightstick', 'sfstick'),
                    ('neomini', 'neomini'),
                ],
                '2020bb': [('snes', 'neomini')],  # neogeo
                'agentx1': [('snes', 'twinstick')],  # twinstick
                'qbert': [('snes', 'qbert')],
                'foobarbaz': [
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
    def test_generate_config_altlayout(
        self,
        generator: Generator,
        rom_name: str,
        control_scheme: str,
        mock_system: Emulator,
        mocker: MockerFixture,
        generate_pads_config: Mock,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                f'/userdata/roms/mame/{rom_name}.zip',
                one_player_controllers,
                {},
                mocker.sentinel.guns,  # pyright: ignore
                mocker.sentinel.wheels,  # pyright: ignore
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        generate_pads_config.assert_called_once_with(
            MAME_CONFIG,
            one_player_controllers,
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
                    'customcfg_dir': 'apple2ee',
                    'pergamecfg_dir': 'apple2ee',
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
                    'customcfg_dir': 'aa4401',
                    'pergamecfg_dir': 'aa4401',
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
                    'customcfg_dir': 'bbcb',
                    'pergamecfg_dir': 'bbcb',
                    'configs': [
                        {'sticktype': ['none', 'acornjoy']},
                        {'altmodel': ['bbcm', 'bbcm512', 'bbcmc']},
                        {'altromtype': ['cass', 'rom1', 'rom2', 'rom3', 'rom4', 'flop2', 'cart1', 'cart2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'camplynx': {
                    'rom': 'rom.bin',
                    'customcfg_dir': 'lynx48k',
                    'pergamecfg_dir': 'lynx48k',
                    'configs': [
                        {'altmodel': ['lynx96k', 'lynx128k']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'cdi': {
                    'rom': 'rom.bin',
                    'customcfg_dir': 'cdimono1',
                    'pergamecfg_dir': 'cdimono1',
                },
                'coco': {
                    'rom': ['rom.rom', 'rom.cas', 'rom.dsk'],
                    'customcfg_dir': 'coco3',
                    'pergamecfg_dir': 'coco3',
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
                    'customcfg_dir': 'electron64',
                    'pergamecfg_dir': 'electron64',
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
                        {'addblankdisk': ['cass', 'flop1', 'flop2']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'fmtowns': {
                    'rom': 'rom.bin',
                    'customcfg_dir': 'fmtmarty',
                    'pergamecfg_dir': 'fmtmarty',
                    'configs': [
                        {'altmodel': ['fmtowns', 'fmtownsux']},
                        {'ramsize': ['2', '4']},
                        # {'addblankdisk': ['0', '1']},
                        {'altromtype': ['flop1', 'flop2', 'hard1']},
                        {'enableui': ['0', '1']},
                    ],
                },
                'gamate': {'rom': 'rom.bin'},
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
                'macintosh': {
                    'rom': 'rom.dsk',
                    'customcfg_dir': 'maclc3',
                    'pergamecfg_dir': 'maclc3',
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
                'pdp1': {
                    'rom': 'rom.tap',
                    'configs': [
                        {'enableui': ['0', '1']},
                    ],
                },
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
                    'pergamecfg_dir': 'ti99_4a',
                    'customcfg_dir': 'ti99_4a',
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
        generator: Generator,
        mock_system: Emulator,
        rom_dir: str,
        rom: str,
        pergamecfg_dir: str,
        customcfg_dir: str,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                f'/userdata/roms/{rom_dir}/{rom}',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (
            MAME_CONFIG / customcfg_dir
            if mock_system.config.get('customcfg', '0') == '0'
            else (MAME_CONFIG / customcfg_dir / 'custom')
        ).is_dir()
        if mock_system.config.get('pergamecfg', '0') == '1':
            assert (MAME_CONFIG / pergamecfg_dir / rom).is_dir()
        else:
            assert not (MAME_CONFIG / pergamecfg_dir / rom).exists()

    @pytest.mark.system_name('adam')
    @pytest.mark.mock_system_config({'softList': 'adam_cart'})
    def test_generate_softlist(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/adam/rom.zip',
                one_player_controllers,
                {},
                {},
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
    def test_generate_softlist_existing_files(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/var/run/mame_software/hash')
        fs.create_symlink('/var/run/mame_software/hash/arcadia.xml', '/usr/bin/mame/hash/arcadia.xml')
        fs.create_symlink('/var/run/mame_software/arcadia', '/userdata/roms/arcadia')

        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/adam/rom.zip',
                one_player_controllers,
                {},
                {},
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
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/mame/some/subdir/rom.zip',
                one_player_controllers,
                {},
                {},
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
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/bbc/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('fm7')
    @pytest.mark.parametrize('mock_system_config', [{'softList': 'fm77av'}, {'softList': 'fm7_cass'}])
    def test_generate_fm7_softlist(
        self,
        generator: Generator,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                '/userdata/roms/fm7/rom.zip',
                one_player_controllers,
                {},
                {},
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
        generator: Generator,
        mock_system: Emulator,
        rom_extension: str,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                f'/userdata/roms/coco/rom.{rom_extension}',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_flop'})
    def test_generate_coco_autorun_xml(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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
                '/userdata/roms/coco/zonx.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_flop'})
    def test_generate_coco_autorun_xml_no_entry(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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
                '/userdata/roms/coco/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('coco')
    @pytest.mark.mock_system_config({'softList': 'coco_cart'})
    def test_generate_coco_autoload_csv(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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
                '/userdata/roms/coco/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.system_name('electron')
    @pytest.mark.mock_system_config({'softList': 'electron_flop'})
    def test_generate_autoload_csv_generic(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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
                '/userdata/roms/electron/rom.zip',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )


def test_generate_pads_config(
    fs: FakeFilesystem, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
) -> None:
    fs.create_dir(MAME_CONFIG)

    generatePadsConfig(
        MAME_CONFIG,
        one_player_controllers,
        '',
        'default',
        False,
        'none',
        None,
        False,
        {},
        False,
        {},
        False,
        False,
        mock_system,
    )

    assert (MAME_CONFIG / 'default.cfg').read_text() == snapshot
