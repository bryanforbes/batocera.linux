# pyright: reportDeprecated=none
from __future__ import annotations

from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BATOCERA_CONF, ES_SETTINGS, ROMS, USER_SHADERS
from configgen.Emulator import Emulator
from configgen.exceptions import MissingEmulator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestEmulator:
    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(
            '/usr/share/batocera/configgen/configgen-defaults.yml',
            contents="""default:
  emulator:
  core:
  options:
    shaderset:          sharp-bilinear-simple
    bezel:              consoles
    arch_option:        none

3ds:
  emulator: citra
  core:     citra
gb:
  emulator: libretro
  core:     gambatte
pcengine:
  emulator: libretro
  core:     pce_fast
n64:
  emulator: mupen64plus
  core:     glide64mk2
""",
        )

        fs.create_file(
            '/usr/share/batocera/configgen/configgen-defaults-arch.yml',
            contents="""default:
  emulator:
  core:
  options:
    hud_support: true
    video_frame_delay_auto: true
    arch_option: arch

pcengine:
  emulator: libretro
  core:     pce
n64:
  options:
    videomode: max-1920x1080
""",
        )

        fs.create_file(
            '/usr/share/batocera/shaders/configs/rendering-defaults.yml',
            contents="""## AUTO = none
default:
  # shader affects retroarch shaders
  shader:
  # scanline affect fba2x
  scanline: false
  # affect gameboy/gambatte (colorization: GB - DMG)
  colorization:
  arch_option: default
  gb_option: default
  gb_arch_option: default

gb:
  gb_option: gb
  gb_arch_option: gb_default
""",
        )

        fs.create_file(
            '/usr/share/batocera/shaders/configs/rendering-defaults-arch.yml',
            contents="""default:
  arch_option: arch

gb:
  gb_arch_option: gb_arch
""",
        )

        fs.create_file(
            '/usr/share/batocera/shaders/configs/sharp-bilinear-simple/rendering-defaults.yml',
            contents="""## SHARP-BILINEAR-SIMPLE
default:
  # shader affects retroarch shaders
  shader: interpolation/sharp-bilinear-simple
  # scanline affect fba2x
  scanline: false
  arch_option: default
  gb_option: default
  gb_arch_option: default

gb:
  gb_option: gb
  gb_arch_option: gb_default
""",
        )

        fs.create_file(
            '/usr/share/batocera/shaders/configs/sharp-bilinear-simple/rendering-defaults-arch.yml',
            contents="""## SHARP-BILINEAR-SIMPLE arch
default:
  arch_option: arch

gb:
  gb_arch_option: gb_arch
""",
        )

        fs.create_file(
            ES_SETTINGS,
            contents="""<?xml version="1.0"?>
<config>
\t<bool name="DrawFramerate" value="true" />
\t<string name="UIMode" value="Full" />
</config>
""",
        )

        return fs

    @pytest.fixture
    def default_args(self) -> Namespace:
        return Namespace(
            system='3ds',
            emulator=None,
            core=None,
            lightgun=False,
            wheel=False,
            netplaymode=None,
            netplaypass=None,
            netplayip=None,
            netplayport=None,
            netplaysession=None,
            state_slot=None,
            autosave=None,
            state_filename=None,
            gameinfoxml='/tmp/game.xml',
        )

    def test_init(self, fs: FakeFilesystem, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
display.brightness=35
controllers.bluetooth.enabled=1
global.batterymode=balanced
global.bezel=none
global.this_should_be_global=global
global.this_should_be_3ds=global
global.this_should_be_folder=global
global.this_should_be_game=global
3ds.this_should_be_3ds=3ds
3ds.this_should_be_folder=3ds
3ds.this_should_be_game=3ds
3ds.folder["/userdata/roms/3ds"].this_should_be_folder=folder
3ds.folder["/userdata/roms/3ds"].this_should_be_game=folder
3ds["rom12.game"].this_should_be_game=game
""",
        )

        emulator = Emulator(default_args, ROMS / '3ds' / 'rom#1=2.game')

        assert emulator.config.data == snapshot
        assert emulator.renderconfig.data == snapshot(name='renderconfig')

        assert emulator.config['this_should_be_global'] == 'global'
        assert emulator.config['this_should_be_3ds'] == '3ds'
        assert emulator.config['this_should_be_folder'] == 'folder'
        assert emulator.config['this_should_be_game'] == 'game'
        assert emulator.game_info_xml == '/tmp/game.xml'

    def test_init_with_arch_defaults(self, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        default_args.system = 'pcengine'
        assert Emulator(default_args, Path()).config.data == snapshot

    def test_init_with_arch_defaults_options(self, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        default_args.system = 'n64'
        assert Emulator(default_args, Path()).config.data == snapshot

    def test_init_shaderset_system(self, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        default_args.system = 'gb'
        emulator = Emulator(default_args, Path())

        assert emulator.config.data == snapshot
        assert emulator.renderconfig.data == snapshot(name='renderconfig')

    @pytest.mark.parametrize('name', ['3ds', 'gb'])
    def test_init_shaderset_none(
        self, default_args: Namespace, name: str, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
global.shaderset=none
""",
        )
        default_args.system = name
        emulator = Emulator(default_args, Path())

        assert emulator.renderconfig.data == snapshot

    @pytest.mark.parametrize('name', ['3ds', 'gb'])
    def test_init_shaderset_user(
        self, default_args: Namespace, name: str, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
global.shaderset=mine
""",
        )

        fs.create_file(
            USER_SHADERS / 'configs' / 'mine' / 'rendering-defaults.yml',
            contents="""
default:
  option: mine_default
  arch_option: mine_default
  gb_option: mine_default
  gb_arch_option: mine_default

gb:
  gb_option: mine_gb
  gb_arch_option: mine_gb_arch
""",
        )

        fs.create_file(
            USER_SHADERS / 'configs' / 'mine' / 'rendering-defaults-arch.yml',
            contents="""default:
  arch_option: mine_arch

gb:
  gb_arch_option: mine_gb_arch
""",
        )
        default_args.system = name

        emulator = Emulator(default_args, Path())

        assert emulator.renderconfig.data == snapshot

    def test_init_emulator_from_batocera_conf(
        self, default_args: Namespace, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
mysystem.emulator=my-emulator
mysystem.core=my-emulator-core
""",
        )

        default_args.system = 'mysystem'
        emulator = Emulator(default_args, Path())

        assert emulator.config.data == snapshot

    def test_init_not_found(self, default_args: Namespace) -> None:
        default_args.system = 'foo'
        with pytest.raises(MissingEmulator):
            Emulator(default_args, Path())

    def test_init_no_defaults_arch_files(
        self, default_args: Namespace, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        fs.remove('/usr/share/batocera/configgen/configgen-defaults-arch.yml')
        fs.remove('/usr/share/batocera/shaders/configs/sharp-bilinear-simple/rendering-defaults-arch.yml')

        default_args.system = 'gb'
        emulator = Emulator(default_args, Path())

        assert emulator.config.data == snapshot
        assert emulator.renderconfig.data == snapshot(name='renderconfig')

    def test_init_no_defaults_arch_files_no_shaderset(
        self, default_args: Namespace, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
global.shaderset=none
""",
        )
        fs.remove('/usr/share/batocera/configgen/configgen-defaults-arch.yml')
        fs.remove('/usr/share/batocera/shaders/configs/rendering-defaults-arch.yml')

        default_args.system = 'gb'
        emulator = Emulator(default_args, Path())

        assert emulator.renderconfig.data == snapshot

    def test_init_no_default_in_defaults_file(self, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        Path('/usr/share/batocera/configgen/configgen-defaults.yml').write_text("""
3ds:
  emulator: 3ds_emulator
  core: 3ds_core
  options:
    3ds_option: 3ds_value
    3ds_arch_option: 3ds_value
""")
        Path('/usr/share/batocera/configgen/configgen-defaults-arch.yml').write_text("""
3ds:
  options:
    3ds_arch_option: 3ds_arch_value
""")

        emulator = Emulator(default_args, Path())

        assert emulator.config.data == snapshot

    @pytest.mark.parametrize('source', ['global', 'system', 'game', 'args'])
    def test_init_forced_emulator(
        self, default_args: Namespace, source: str, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        if source in ['global', 'system', 'game']:
            prefix = 'global' if source == 'global' else '3ds'
            if source == 'game':
                prefix = f'{prefix}["rom12.game"]'

            fs.create_file(
                BATOCERA_CONF,
                contents=f"""# Mock conf file
{prefix}.emulator=blah
""",
            )
        else:
            default_args.emulator = 'blah'

        assert Emulator(default_args, ROMS / '3ds' / 'rom#1=2.game').config.data == snapshot

    @pytest.mark.parametrize('source', ['global', 'system', 'game', 'args'])
    def test_init_forced_core(
        self, default_args: Namespace, source: str, fs: FakeFilesystem, snapshot: SnapshotAssertion
    ) -> None:
        if source in ['global', 'system', 'game']:
            prefix = 'global' if source == 'global' else '3ds'
            if source == 'game':
                prefix = f'{prefix}["rom12.game"]'

            fs.create_file(
                BATOCERA_CONF,
                contents=f"""# Mock conf file
{prefix}.core=blah
""",
            )
        else:
            default_args.core = 'blah'

        assert Emulator(default_args, ROMS / '3ds' / 'rom#1=2.game').config.data == snapshot

    @pytest.mark.parametrize('lightgun', [False, True])
    @pytest.mark.parametrize('config_value', [None, '0', '1'])
    def test_init_use_guns(
        self,
        fs: FakeFilesystem,
        default_args: Namespace,
        config_value: str | None,
        lightgun: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        if config_value is not None:
            fs.create_file(
                BATOCERA_CONF,
                contents=f"""# Mock conf file
global.use_guns={config_value}
""",
            )
        default_args.lightgun = lightgun

        assert Emulator(default_args, Path()).config.data == snapshot

    @pytest.mark.parametrize('wheel', [False, True])
    @pytest.mark.parametrize('config_value', [None, '0', '1'])
    def test_load_configs_use_wheels(
        self,
        fs: FakeFilesystem,
        default_args: Namespace,
        config_value: str | None,
        wheel: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        if config_value is not None:
            fs.create_file(
                BATOCERA_CONF,
                contents=f"""# Mock conf file
global.use_wheels={config_value}
""",
            )
        default_args.wheel = wheel

        assert Emulator(default_args, Path()).config.data == snapshot

    @pytest.mark.parametrize(
        'arg',
        [
            'netplaymode',
            'netplaypass',
            'netplayip',
            'netplayport',
            'netplaysession',
            'state_slot',
            'autosave',
            'state_filename',
        ],
    )
    def test_load_configs_args(self, default_args: Namespace, arg: str, snapshot: SnapshotAssertion) -> None:
        setattr(default_args, arg, 'value')

        assert Emulator(default_args, Path()).config.data == snapshot

    @pytest.mark.parametrize('ui_mode', ['Full', 'Kiosk', 'Kid', 'bar', None])
    @pytest.mark.parametrize('draw_framerate', ['true', 'false', 'foo', None])
    def test_init_es_settings(
        self, default_args: Namespace, draw_framerate: str | None, ui_mode: str | None, snapshot: SnapshotAssertion
    ) -> None:
        ES_SETTINGS.write_text(f"""<?xml version="1.0"?>
<config>
\t<string name="DrawFramerate" value="true" />
\t<bool name="UIMode" value="true" />
{f'\t<bool name="DrawFramerate" value="{draw_framerate}" />' if draw_framerate is not None else ''}
{f'\t<string name="UIMode" value="{ui_mode}" />' if ui_mode is not None else ''}
\t<bool name="EnableSounds" value="true" />
</config>
""")

        assert Emulator(default_args, Path()).config.data == snapshot

    def test_init_es_settings_parse_error(self, default_args: Namespace, snapshot: SnapshotAssertion) -> None:
        ES_SETTINGS.unlink()

        assert Emulator(default_args, Path()).config.data == snapshot

    def test_is_opt_set(self, default_args: Namespace) -> None:
        emulator = Emulator(default_args, Path())

        assert emulator.isOptSet('hud_support')
        assert not emulator.isOptSet('foo')

    def test_get_opt_boolean(self, default_args: Namespace, fs: FakeFilesystem) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
global.zero=0
global.one=1
global.true=tRuE
global.false=fAlSe
global.on=on
global.off=off
global.enabled=enabled
global.disabled=disabled
global.foo=foo
""",
        )
        emulator = Emulator(default_args, Path())

        assert emulator.getOptBoolean('hud_support')
        assert emulator.getOptBoolean('one')
        assert emulator.getOptBoolean('true')
        assert emulator.getOptBoolean('on')
        assert emulator.getOptBoolean('enabled')
        assert not emulator.getOptBoolean('core-forced')
        assert not emulator.getOptBoolean('zero')
        assert not emulator.getOptBoolean('false')
        assert not emulator.getOptBoolean('off')
        assert not emulator.getOptBoolean('disabled')
        assert not emulator.getOptBoolean('foo')
        assert not emulator.getOptBoolean('bar')

    def test_get_opt_string(self, default_args: Namespace, fs: FakeFilesystem) -> None:
        fs.create_file(
            BATOCERA_CONF,
            contents="""# Mock conf file
global.value=something
global.novalue=
""",
        )
        emulator = Emulator(default_args, Path())

        assert emulator.getOptString('value') == 'something'
        assert emulator.getOptString('novalue') == ''
        assert emulator.getOptString('nonexistentvalue') == ''

    @pytest.mark.parametrize('borders_mode', [None, 'normal', 'hidden'])
    @pytest.mark.parametrize('es_borders_mode', [None, 'auto', 'normal', 'gameonly', 'hidden'])
    @pytest.mark.parametrize('borders_size', [None, 'auto', 'thin', 'medium', 'big'])
    @pytest.mark.parametrize(
        'guns',
        [
            pytest.param([], id='no guns'),
            pytest.param([False, False], id='guns borders not required'),
            pytest.param([False, True], id='guns borders required'),
        ],
    )
    def test_guns_borders_size_name(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        guns: list[bool],
        borders_size: str | None,
        es_borders_mode: str | None,
        borders_mode: str | None,
        snapshot: SnapshotAssertion,
    ) -> None:
        emulator = Emulator(default_args, Path())

        if borders_size is not None:
            emulator.config['controllers.guns.borderssize'] = borders_size

        if es_borders_mode is not None:
            emulator.config['controllers.guns.bordersmode'] = es_borders_mode

        if borders_mode is not None:
            emulator.config['bordersmode'] = borders_mode

        assert emulator.guns_borders_size_name([mocker.Mock(needs_borders=value) for value in guns]) == snapshot

    @pytest.mark.parametrize('value', [None, 'foo', '4:3'])
    def test_guns_border_ratio_type(self, default_args: Namespace, value: str | None) -> None:
        emulator = Emulator(default_args, Path())

        if value:
            emulator.config['controllers.guns.bordersratio'] = value

        assert emulator.guns_border_ratio_type([]) == value

    @pytest.mark.parametrize('line_to_omit', [None, 'name', 'thumbnail'])
    def test_es_game_info(
        self, fs: FakeFilesystem, default_args: Namespace, line_to_omit: str | None, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(
            '/tmp/game.xml',
            contents=f"""<?xml version="1.0"?>
    <gameList parentHash="0">
            <game>
                    <path>/userdata/roms/system/rom.zip</path>
                    {'' if line_to_omit == 'name' else '<name>My custom rom</name>'}
                    <image>/userdata/roms/system/images/My custom rom-image.png</image>
                    {
                ''
                if line_to_omit == 'thumbnail'
                else '<thumbnail>/userdata/roms/system/images/My custom rom-thumb.png</thumbnail>'
            }
                    <playcount>3</playcount>
                    <lastplayed>20250209T152311</lastplayed>
                    <gametime>0</gametime>
                    <lang>en</lang>
            </game>
    </gameList>""",
        )

        emulator = Emulator(default_args, Path())

        assert emulator.es_game_info == snapshot

    def test_es_game_info_invalid_xml(self, default_args: Namespace, fs: FakeFilesystem) -> None:
        fs.create_file('/tmp/game.xml')

        emulator = Emulator(default_args, Path())

        assert emulator.es_game_info == {}
