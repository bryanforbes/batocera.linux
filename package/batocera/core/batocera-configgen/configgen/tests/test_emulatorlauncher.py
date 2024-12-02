from __future__ import annotations

import json
import logging
import os
import stat
from argparse import Namespace
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast

import pytest
from pytest_lazy_fixtures import lf
from syrupy.filters import paths

from configgen.batoceraPaths import ROMS, SAVES, SYSTEM_SCRIPTS, USER_SCRIPTS
from configgen.Command import Command
from configgen.exceptions import BadCommandLineArguments
from tests.mock_emulator import MockEmulator

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from unittest.mock import MagicMock, Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


pytestmark = pytest.mark.usefixtures('fs')


@pytest.fixture(autouse=True)
def profiler(mocker: MockerFixture) -> MagicMock:
    mock_profiler = mocker.MagicMock()
    mocker.patch.dict('sys.modules', values={'configgen.profiler': mock_profiler})
    return mock_profiler


@pytest.fixture
def squashfs_rom(mocker: MockerFixture) -> Mock:
    mock_context_manager = mocker.MagicMock()
    mock_context_manager.__enter__.return_value = mocker.sentinel.rom
    return mocker.patch('configgen.utils.squashfs.squashfs_rom', return_value=mock_context_manager)


@pytest.fixture
def get_bezel_infos(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.bezels.getBezelInfos', return_value=None)


@pytest.fixture
def default_config() -> dict[str, Any]:
    return {
        'emulator': 'default-emulator',
        'emulator-forced': False,
        'core': 'default-core',
        'core-forced': False,
        'hud_support': True,
        'videomode': 'default',
        'ratio': 'auto',
        'videothreaded': False,
        'smooth': True,
        'shaderset': 'sharp-bilinear-simple',
        'rewind': False,
        'bezel': 'consoles',
        'forceNoBezel': False,
        'gamemode_enable': False,
    }


@pytest.fixture
def mock_system(default_config: dict[str, Any]) -> MockEmulator:
    return MockEmulator('', default_config.copy(), {})


@pytest.fixture
def os_environ(mocker: MockerFixture) -> None:
    mocker.patch.dict('os.environ', values={}, clear=True)


@pytest.fixture
def generator(mocker: MockerFixture) -> Mock:
    mock = mocker.Mock()

    def get_resolution_mode_side_effect(config: dict[str, Any]) -> str:
        return config['videomode']

    mock.getResolutionMode.side_effect = get_resolution_mode_side_effect
    mock.getMouseMode.return_value = False
    mock.executionDirectory.return_value = None
    mock.supportsInternalBezels.return_value = False
    mock.hasInternalMangoHUDCall.return_value = False
    mock.getInGameRatio.return_value = 4 / 3

    return mock


def test_profile_enabled_on_import(profiler: Mock) -> None:
    import configgen.emulatorlauncher  # noqa: F401

    profiler.start.assert_called_once_with()


def test_main(mocker: MockerFixture, squashfs_rom: Mock) -> None:
    from configgen.emulatorlauncher import main

    start_rom = mocker.patch('configgen.emulatorlauncher.start_rom', return_value=mocker.sentinel.start_rom_result)
    args = mocker.Mock(rom=ROMS / 'foo' / 'bar.zip')

    assert main(args, 10) == mocker.sentinel.start_rom_result

    squashfs_rom.assert_not_called()
    start_rom.assert_called_once_with(args, 10, ROMS / 'foo' / 'bar.zip', ROMS / 'foo' / 'bar.zip')


def test_main_squashfs(mocker: MockerFixture, squashfs_rom: Mock) -> None:
    from configgen.emulatorlauncher import main

    start_rom = mocker.patch('configgen.emulatorlauncher.start_rom', return_value=mocker.sentinel.start_rom_result)
    args = mocker.Mock(rom=ROMS / 'foo' / 'bar.squashfs')

    assert main(args, 10) == mocker.sentinel.start_rom_result

    squashfs_rom.assert_called_once_with(ROMS / 'foo' / 'bar.squashfs')
    start_rom.assert_called_once_with(args, 10, mocker.sentinel.rom, ROMS / 'foo' / 'bar.squashfs')


class TestGetHudBezel:
    @pytest.fixture(autouse=True)
    def bezels_util_create_transparent_bezel(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.bezels.createTransparentBezel')

    @pytest.fixture(autouse=True)
    def bezels_util_fast_image_size(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.bezels.fast_image_size')

    @pytest.fixture(autouse=True)
    def bezels_util_resize_image(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.bezels.resizeImage')

    @pytest.fixture(autouse=True)
    def bezels_util_tattoo_image(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.bezels.tatooImage')

    @pytest.fixture(autouse=True)
    def bezels_util_gun_borders_size(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.utils.bezels.gunBordersSize',
            return_value=(mocker.sentinel.inner_size, mocker.sentinel.outer_size),
        )

    @pytest.fixture(autouse=True)
    def bezels_util_guns_borders_color_fom_config(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.utils.bezels.gunsBordersColorFomConfig', return_value=mocker.sentinel.borders_color
        )

    @pytest.fixture(autouse=True)
    def bezels_util_gun_border_image(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.bezels.gunBorderImage', return_value=None)

    @pytest.mark.parametrize('borders_size', [None, 'medium'])
    @pytest.mark.parametrize('bezel_tattoo', [None, 'system'])
    def test_get(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generator: Mock,
        get_bezel_infos: Mock,
        bezel_tattoo: str | None,
        borders_size: str | None,
        bezels_util_tattoo_image: Mock,
        bezels_util_gun_border_image: Mock,
        bezels_util_gun_borders_size: Mock,
        bezels_util_guns_borders_color_fom_config: Mock,
        bezels_util_create_transparent_bezel: Mock,
        bezels_util_fast_image_size: Mock,
        bezels_util_resize_image: Mock,
    ) -> None:
        mock_system.name = 'dreamcast'

        if bezel_tattoo is not None:
            mock_system.config['bezel.tattoo'] = bezel_tattoo

        fs.create_file(
            '/userdata/mybezels/dreamcast.info',
            contents="""{
 "width":1920,
 "height":1080,
 "top":24,
 "left":273,
 "bottom":24,
 "right":273,
 "opacity":1.0000000,
 "messagex":0.220000,
 "messagey":0.120000
}
""",
        )

        get_bezel_infos.return_value = {
            'info': Path('/userdata/mybezels/dreamcast.info'),
            'png': Path('/userdata/mybezels/dreamcast.png'),
        }

        from configgen.emulatorlauncher import getHudBezel

        hud_bezel = getHudBezel(
            mock_system, generator, Path('/path/to/rom.zip'), {'width': 1920, 'height': 1080}, borders_size, None
        )

        assert hud_bezel is not None
        assert hud_bezel == Path(
            '/tmp/bezel_gunborders.png'
            if borders_size is not None
            else '/tmp/bezel_tattooed.png'
            if bezel_tattoo is not None
            else '/userdata/mybezels/dreamcast.png'
        )
        get_bezel_infos.assert_called_once_with(Path('/path/to/rom.zip'), 'consoles', 'dreamcast', 'default-emulator')
        if bezel_tattoo:
            bezels_util_tattoo_image.assert_called_once_with(
                Path('/userdata/mybezels/dreamcast.png'), Path('/tmp/bezel_tattooed.png'), mock_system
            )
        else:
            bezels_util_tattoo_image.assert_not_called()

        if borders_size:
            bezels_util_gun_borders_size.assert_called_once_with(borders_size)
            bezels_util_guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
            bezels_util_gun_border_image.assert_called_once_with(
                Path('/tmp/bezel_tattooed.png') if bezel_tattoo else Path('/userdata/mybezels/dreamcast.png'),
                Path('/tmp/bezel_gunborders.png'),
                None,
                mocker.sentinel.inner_size,
                mocker.sentinel.outer_size,
                mocker.sentinel.borders_color,
            )
        else:
            bezels_util_gun_borders_size.assert_not_called()
            bezels_util_guns_borders_color_fom_config.assert_not_called()
            bezels_util_gun_border_image.assert_not_called()

        bezels_util_create_transparent_bezel.assert_not_called()
        bezels_util_fast_image_size.assert_not_called()
        bezels_util_resize_image.assert_not_called()

    @pytest.mark.parametrize(
        ('bezel', 'bezel_tattoo', 'borders_size'),
        (
            (bezel, bezel_tattoo, borders_size)
            for bezel in [False, '', 'none']
            for bezel_tattoo, borders_size in [('system', False), (False, 'medium')]
        ),
    )
    def test_transparent(
        self,
        mocker: MockerFixture,
        mock_system: Emulator,
        bezel: str | Literal[False],
        bezel_tattoo: str | Literal[False],
        borders_size: str | Literal[False],
        generator: Mock,
        bezels_util_create_transparent_bezel: Mock,
        bezels_util_tattoo_image: Mock,
        bezels_util_gun_border_image: Mock,
        bezels_util_gun_borders_size: Mock,
        bezels_util_guns_borders_color_fom_config: Mock,
    ) -> None:
        if bezel is False:
            del mock_system.config['bezel']
        else:
            mock_system.config['bezel'] = bezel

        if bezel_tattoo is not False:
            mock_system.config['bezel.tattoo'] = bezel_tattoo

        from configgen.emulatorlauncher import getHudBezel

        hud_bezel = getHudBezel(
            mock_system, generator, Path(), {'width': 640, 'height': 360}, borders_size or None, None
        )

        assert hud_bezel is not None
        assert hud_bezel == Path('/tmp') / (
            'bezel_gunborders.png'
            if borders_size
            else 'bezel_tattooed.png'
            if bezel_tattoo
            else 'bezel_transhud_black.png'
        )

        bezels_util_create_transparent_bezel.assert_called_once_with(Path('/tmp/bezel_transhud_black.png'), 640, 360)

        if bezel_tattoo:
            bezels_util_tattoo_image.assert_called_once_with(
                Path('/tmp/bezel_transhud_black.png'), Path('/tmp/bezel_tattooed.png'), mock_system
            )
        else:
            bezels_util_tattoo_image.assert_not_called()

        if borders_size:
            bezels_util_gun_borders_size.assert_called_once_with(borders_size)
            bezels_util_guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
            bezels_util_gun_border_image.assert_called_once_with(
                Path('/tmp/bezel_tattooed.png') if bezel_tattoo else Path('/tmp/bezel_transhud_black.png'),
                Path('/tmp/bezel_gunborders.png'),
                None,
                mocker.sentinel.inner_size,
                mocker.sentinel.outer_size,
                mocker.sentinel.borders_color,
            )
        else:
            bezels_util_gun_borders_size.assert_not_called()
            bezels_util_guns_borders_color_fom_config.assert_not_called()
            bezels_util_gun_border_image.assert_not_called()

    @pytest.mark.parametrize('stretch', [True, False])
    @pytest.mark.parametrize('borders_size', [None, 'medium'])
    @pytest.mark.parametrize('bezel_tattoo', [None, 'system'])
    def test_resize(
        self,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        generator: Mock,
        mock_system: Emulator,
        get_bezel_infos: Mock,
        stretch: bool,
        bezel_tattoo: str | None,
        borders_size: str | None,
        bezels_util_resize_image: Mock,
        bezels_util_tattoo_image: Mock,
        bezels_util_gun_border_image: Mock,
        bezels_util_gun_borders_size: Mock,
        bezels_util_guns_borders_color_fom_config: Mock,
    ) -> None:
        mock_system.config['bezel_stretch'] = '1' if stretch else '0'

        if bezel_tattoo is not None:
            mock_system.config['bezel.tattoo'] = bezel_tattoo

        fs.create_file(
            '/userdata/mybezels/dreamcast.info',
            contents="""{
 "width":1920,
 "height":1080,
 "top":24,
 "left":273,
 "bottom":24,
 "right":273,
 "opacity":1.0000000,
 "messagex":0.220000,
 "messagey":0.120000
}
""",
        )

        get_bezel_infos.return_value = {
            'info': Path('/userdata/mybezels/dreamcast.info'),
            'png': Path('/userdata/mybezels/dreamcast.png'),
        }

        from configgen.emulatorlauncher import getHudBezel

        hud_bezel = getHudBezel(
            mock_system, generator, Path('/path/to/rom.zip'), {'width': 1440, 'height': 810}, borders_size, None
        )

        assert hud_bezel is not None
        assert hud_bezel == Path(
            '/tmp/bezel_gunborders.png'
            if borders_size is not None
            else '/tmp/bezel_tattooed.png'
            if bezel_tattoo is not None
            else '/tmp/bezel.png'
        )
        bezels_util_resize_image.assert_called_once_with(
            Path('/userdata/mybezels/dreamcast.png'), Path('/tmp/bezel.png'), 1440, 810, stretch
        )
        if bezel_tattoo:
            bezels_util_tattoo_image.assert_called_once_with(
                Path('/tmp/bezel.png'), Path('/tmp/bezel_tattooed.png'), mock_system
            )
        else:
            bezels_util_tattoo_image.assert_not_called()
        if borders_size:
            bezels_util_gun_borders_size.assert_called_once_with(borders_size)
            bezels_util_guns_borders_color_fom_config.assert_called_once_with(mock_system.config)
            bezels_util_gun_border_image.assert_called_once_with(
                Path('/tmp/bezel_tattooed.png') if bezel_tattoo else Path('/tmp/bezel.png'),
                Path('/tmp/bezel_gunborders.png'),
                None,
                mocker.sentinel.inner_size,
                mocker.sentinel.outer_size,
                mocker.sentinel.borders_color,
            )
        else:
            bezels_util_gun_borders_size.assert_not_called()
            bezels_util_guns_borders_color_fom_config.assert_not_called()
            bezels_util_gun_border_image.assert_not_called()

    def test_resize_fails(
        self,
        fs: FakeFilesystem,
        generator: Mock,
        mock_system: Emulator,
        get_bezel_infos: Mock,
        bezels_util_resize_image: Mock,
    ) -> None:
        fs.create_file(
            '/path/to/bezel/file.info',
            contents=json.dumps({'width': 1440, 'height': 810}),
        )

        get_bezel_infos.return_value = {
            'info': Path('/path/to/bezel/file.info'),
            'png': Path('/path/to/bezel/file.png'),
        }

        bezels_util_resize_image.side_effect = Exception('Test error')

        from configgen.emulatorlauncher import getHudBezel

        assert (
            getHudBezel(mock_system, generator, Path('/path/to/rom.zip'), {'width': 1920, 'height': 1080}, None, None)
            is None
        )
        bezels_util_resize_image.assert_called_once_with(
            Path('/path/to/bezel/file.png'), Path('/tmp/bezel.png'), 1920, 1080, False
        )

    def test_supports_internal_bezels(
        self,
        generator: Mock,
        mock_system: Emulator,
    ) -> None:
        generator.supportsInternalBezels.return_value = True

        from configgen.emulatorlauncher import getHudBezel

        assert getHudBezel(mock_system, generator, Path(), {'width': 1920, 'height': 1080}, None, None) is None

    @pytest.mark.parametrize('bezel_tattoo', [None, '0'])
    @pytest.mark.parametrize('bezel', [None, '', 'none'])
    def test_no_bezel_tattoo_and_borders_size(
        self,
        generator: Mock,
        mock_system: Emulator,
        bezel: str | None,
        bezel_tattoo: str | None,
    ) -> None:
        if bezel is None:
            del mock_system.config['bezel']
        else:
            mock_system.config['bezel'] = bezel

        if bezel_tattoo is not None:
            mock_system.config['bezel.tattoo'] = bezel_tattoo

        from configgen.emulatorlauncher import getHudBezel

        assert getHudBezel(mock_system, generator, Path(), {'width': 1920, 'height': 1080}, None, None) is None

    @pytest.mark.usefixtures('get_bezel_infos')
    def test_no_bezel_info(self, generator: Mock, mock_system: Emulator, get_bezel_infos: Mock) -> None:
        from configgen.emulatorlauncher import getHudBezel

        mock_system.name = 'system-name'

        assert (
            getHudBezel(
                mock_system, generator, Path('/path/to/rom.zip'), {'width': 1920, 'height': 1080}, 'medium', None
            )
            is None
        )
        get_bezel_infos.assert_called_once_with(Path('/path/to/rom.zip'), 'consoles', 'system-name', 'default-emulator')

    @pytest.mark.parametrize(
        ('info_exists', 'has_size'), [(True, True), (True, False), (True, None), (False, True), (False, False)]
    )
    def test_screen_and_bezel_ratio_do_not_match(
        self,
        fs: FakeFilesystem,
        generator: Mock,
        mock_system: Emulator,
        get_bezel_infos: Mock,
        info_exists: bool,
        has_size: bool | None,
        bezels_util_fast_image_size: Mock,
    ) -> None:
        if info_exists:
            fs.create_file(
                '/path/to/bezel/file.info',
                contents="""{
        "width": 1920,
        "height": 1087
    }"""
                if has_size
                else ''
                if has_size is None
                else '{}',
            )

        if not info_exists or not has_size:
            bezels_util_fast_image_size.return_value = (1920, 1087)

        get_bezel_infos.return_value = {
            'info': Path('/path/to/bezel/file.info'),
            'png': Path('/path/to/bezel/file.png'),
        }

        from configgen.emulatorlauncher import getHudBezel

        assert (
            getHudBezel(mock_system, generator, Path('/path/to/rom.zip'), {'width': 1920, 'height': 1080}, None, None)
            is None
        )
        get_bezel_infos.assert_called_once_with(Path('/path/to/rom.zip'), 'consoles', '', 'default-emulator')
        if not info_exists or not has_size:
            bezels_util_fast_image_size.assert_called_once_with(Path('/path/to/bezel/file.png'))
        else:
            bezels_util_fast_image_size.assert_not_called()

    @pytest.mark.parametrize(
        'extra_info',
        [
            {'top': 55},
            {'top': 54, 'bottom': 55},
            {'bottom': 55},
            {'left': 313},
            {'top': 54, 'bottom': 54, 'left': 313},
            {'right': 313},
            {'top': 54, 'bottom': 54, 'left': 312, 'right': 313},
        ],
        ids=str,
    )
    def test_bezel_covers_too_much_game(
        self,
        fs: FakeFilesystem,
        generator: Mock,
        mock_system: Emulator,
        get_bezel_infos: Mock,
        extra_info: dict[str, int],
    ) -> None:
        fs.create_file(
            '/path/to/bezel/file.info',
            contents=json.dumps({'width': 1920, 'height': 1080, **extra_info}),
        )

        get_bezel_infos.return_value = {
            'info': Path('/path/to/bezel/file.info'),
            'png': Path('/path/to/bezel/file.png'),
        }

        from configgen.emulatorlauncher import getHudBezel

        assert (
            getHudBezel(mock_system, generator, Path('/path/to/rom.zip'), {'width': 1920, 'height': 1080}, None, None)
            is None
        )
        get_bezel_infos.assert_called_once_with(Path('/path/to/rom.zip'), 'consoles', '', 'default-emulator')


def test_call_external_scripts(fs: FakeFilesystem, subprocess_call: Mock, snapshot: SnapshotAssertion) -> None:
    fs.create_file('/path/to/scripts/script1.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/sub_dir/subscript1.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/sub_dir/sub_sub_dir/subscript2.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/script2.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/script3.sh')

    from configgen.emulatorlauncher import callExternalScripts

    callExternalScripts(Path('/path/to/scripts'), 'my_event', ['foo', 'bar', Path('/my/stuff')])

    assert subprocess_call.call_args_list == snapshot


def test_call_external_scripts_not_directory(fs: FakeFilesystem, subprocess_call: Mock) -> None:
    fs.create_file('/path/to/scripts/script1.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/sub_dir/subscript1.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/sub_dir/sub_sub_dir/subscript2.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/script2.sh', st_mode=stat.S_IXUSR)
    fs.create_file('/path/to/scripts/script3.sh')

    from configgen.emulatorlauncher import callExternalScripts

    callExternalScripts(Path('/path/to/scripts/script1.sh'), 'my_event', ['foo', 'bar', Path('/my/stuff')])

    subprocess_call.assert_not_called()


@pytest.mark.parametrize('hud_value', [None, 'none'])
def test_get_hud_config_no_hud_has_bezel(
    mock_system: Emulator, hud_value: str | None, snapshot: SnapshotAssertion
) -> None:
    if hud_value:
        mock_system.config['hud'] = hud_value

    from configgen.emulatorlauncher import getHudConfig

    assert (
        getHudConfig(
            mock_system,
            'System Name',
            'default-emulator',
            'effective-core',
            Path('rom-path'),
            Path('/path/to/bezel.png'),
        )
        == snapshot
    )


def _get_hud_params(hud: str) -> Iterator[tuple[str, str, None, Mapping[str, str], str, str]]:
    for corner in ['', 'NW', 'NE', 'SE', 'SW']:
        for info in [{}, {'name': 'GAMENAME'}, {'thumbnail': 'GAMETHUMBNAIL'}]:
            for emulator, core in [('default_emulator', 'effective_core'), ('emulator_name', 'emulator_name')]:
                yield (hud, corner, None, info, emulator, core)


@pytest.mark.parametrize('bezel', [None, '/path/to/bezel'])
@pytest.mark.parametrize(
    ('hud', 'hud_corner', 'hud_custom', 'gameinfos', 'emulator', 'core'),
    [
        *_get_hud_params('game'),
        *_get_hud_params('perf'),
        ('custom', '', '', {}, '', ''),
        ('custom', '', 'my_custom_stuff', {}, '', ''),
        (
            'custom',
            '',
            'my_custom_stuff\n%THUMBNAIL%\n%SYSTEMNAME%\n%GAMENAME%\n%EMULATORCORE%',
            {'name': 'GAMENAME', 'thumbnail': 'THUMBNAIL'},
            'emulator',
            'core',
        ),
        (
            'custom',
            '',
            'my_custom_stuff\n%THUMBNAIL%\n%SYSTEMNAME%\n%GAMENAME%\n%EMULATORCORE%',
            {'name': 'GAMENAME', 'thumbnail': 'THUMBNAIL'},
            'emulator',
            'emulator',
        ),
    ],
    ids=str,
)
def test_get_hud_config_has_hud(
    mock_system: Emulator,
    hud: str,
    hud_custom: str | None,
    hud_corner: str,
    gameinfos: dict[str, str],
    emulator: str,
    core: str,
    bezel: str | None,
    snapshot: SnapshotAssertion,
) -> None:
    from configgen.emulatorlauncher import getHudConfig

    mock_system.config['hud'] = hud
    mock_system.config['hud_corner'] = hud_corner
    cast('MockEmulator', mock_system).es_game_info = gameinfos

    if hud_custom:
        mock_system.config['hud_custom'] = hud_custom

    assert (
        getHudConfig(
            mock_system,
            'System Name',
            emulator,
            core,
            Path('rom-path'),
            None if bezel is None else Path(bezel),
        )
        == snapshot
    )


@pytest.mark.usefixtures('os_environ')
def test_run_command(
    mocker: MockerFixture, subprocess_popen: Mock, snapshot: SnapshotAssertion, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)

    mock_popen = mocker.Mock()
    mock_popen.communicate.return_value = (b'output', b'error')
    mock_popen.returncode = mocker.sentinel.popen_returncode

    subprocess_popen.return_value = mock_popen

    from configgen.emulatorlauncher import runCommand

    assert runCommand(Command(['command', 'arg1', 'arg2'], {'ENV_VAR_1': '1'})) == mocker.sentinel.popen_returncode
    assert subprocess_popen.call_args_list == snapshot(
        exclude=paths('0.1.env.PYTEST_CURRENT_TEST', '0.1.env.COV_CORE_CONTEXT')
    )
    assert caplog.record_tuples == snapshot(name='logging')


def test_run_command_no_commands(subprocess_popen: Mock) -> None:
    from configgen.emulatorlauncher import runCommand

    with pytest.raises(BadCommandLineArguments):
        runCommand(Command([], {'ENV_VAR_1': '1'}))

    subprocess_popen.assert_not_called()


@pytest.mark.parametrize('exception', [BrokenPipeError(), Exception('Test exception')])
def test_run_command_error_handling(mocker: MockerFixture, exception: Exception, subprocess_popen: Mock) -> None:
    from configgen.emulatorlauncher import runCommand

    mock_popen = mocker.Mock()
    mock_popen.communicate.side_effect = exception

    subprocess_popen.return_value = mock_popen

    assert runCommand(Command(['command'], {})) == 0 if isinstance(exception, BrokenPipeError) else 200


class TestStartRom:
    @pytest.fixture(autouse=True)
    def controller_load_for_players(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.controller.Controller.load_for_players', return_value=mocker.sentinel.player_controllers
        )

    @pytest.fixture(autouse=True)
    def controllers_get_games_metadata(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.controllersConfig.getGamesMetaData', return_value=mocker.sentinel.metadata)

    @pytest.fixture(autouse=True)
    def gun_get_and_precalibrate_all(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.gun.Gun.get_and_precalibrate_all', return_value=mocker.sentinel.precalibrated_guns
        )

    @pytest.fixture(autouse=True)
    def controllers_get_devices_information(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.controllersConfig.getDevicesInformation', return_value=mocker.sentinel.get_devices_information
        )

    @pytest.fixture(autouse=True)
    def system_guns_borders_size_name(self, mocker: MockerFixture, mock_system: Emulator) -> Mock:
        return mocker.patch.object(
            mock_system, 'guns_borders_size_name', return_value=mocker.sentinel.guns_borders_size_name
        )

    @pytest.fixture(autouse=True)
    def system_guns_border_ratio_type(self, mocker: MockerFixture, mock_system: Emulator) -> Mock:
        return mocker.patch.object(
            mock_system, 'guns_border_ratio_type', return_value=mocker.sentinel.guns_border_ratio_type
        )

    @pytest.fixture
    def default_args(self) -> Namespace:
        return Namespace(
            system='system_name',
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
            gameinfoxml=None,
            systemname=None,
        )

    @pytest.fixture(autouse=True)
    def emulator_class(self, mocker: MockerFixture, mock_system: MockEmulator) -> Mock:
        mock = mocker.patch('configgen.Emulator.Emulator')

        def emulator_side_effect(args: Namespace, *_args: Any, **kwargs: Any) -> MockEmulator:
            mock_system.name = args.system
            return mock_system

        mock.side_effect = emulator_side_effect

        return mock

    @pytest.fixture
    def mock_command(self) -> Command:
        return Command([], {})

    @pytest.fixture
    def generator(self, generator: Mock, mock_command: Command) -> Mock:
        generator.generate.return_value = mock_command
        return generator

    @pytest.fixture(autouse=True)
    def get_generator(self, mocker: MockerFixture, generator: Mock) -> Mock:
        return mocker.patch('configgen.generators.get_generator', return_value=generator)

    @pytest.fixture(autouse=True)
    def evmapy(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.evmapy.evmapy')

    @pytest.fixture(autouse=True)
    def set_hotkeygen_context(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.hotkeygen.set_hotkeygen_context')

    @pytest.fixture(autouse=True)
    def wheels_utils_configure_wheels(self, mocker: MockerFixture) -> Mock:
        configure_wheels = mocker.patch('configgen.utils.wheelsUtils.configure_wheels')
        configure_wheels.return_value.__enter__.return_value = (
            mocker.sentinel.new_player_controllers,
            mocker.sentinel.wheels,
        )
        return configure_wheels

    @pytest.fixture(autouse=True)
    def video_mode_get_current_mode(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.videoMode.getCurrentMode', return_value='1920x1080.60.00')

    @pytest.fixture(autouse=True)
    def video_mode_get_current_resolution(self, mocker: MockerFixture) -> Mock:
        return mocker.patch(
            'configgen.utils.videoMode.getCurrentResolution', return_value={'width': 1920, 'height': 1080}
        )

    @pytest.fixture(autouse=True)
    def video_mode_min_to_max_resolution(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.videoMode.minTomaxResolution')

    @pytest.fixture(autouse=True)
    def video_mode_change_mode(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.videoMode.changeMode')

    @pytest.fixture(autouse=True)
    def video_mode_is_resolution_reversed(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.videoMode.isResolutionReversed', return_value=False)

    @pytest.fixture(autouse=True)
    def video_mode_change_mouse(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('configgen.utils.videoMode.changeMouse')

    def test_call(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        emulator_class: Mock,
        mock_system: Emulator,
        default_config: dict[str, Any],
        profiler: Mock,
        controllers_get_games_metadata: Mock,
        gun_get_and_precalibrate_all: Mock,
        wheels_utils_configure_wheels: Mock,
        get_generator: Mock,
        generator: Mock,
        video_mode_change_mode: Mock,
        evmapy: Mock,
        set_hotkeygen_context: Mock,
        system_guns_borders_size_name: Mock,
        system_guns_border_ratio_type: Mock,
        video_mode_change_mouse: Mock,
        mock_command: Command,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        call_external_scripts = mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        run_command = mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        get_hud_bezel = mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)
        get_hud_config = mocker.patch('configgen.emulatorlauncher.getHudConfig')

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        assert mock_system.config.data == {
            **default_config,
            'sdlvsync': '1',
        }
        assert os.environ['SDL_RENDER_VSYNC'] == '1'

        emulator_class.assert_called_once_with(default_args, ROMS / 'foo' / 'bar.squashfs')
        controllers_get_games_metadata.assert_called_once_with('system_name', Path('/var/squashfs/bar/bar.zip'))
        gun_get_and_precalibrate_all.assert_called_once_with(mock_system, Path('/var/squashfs/bar/bar.zip'))
        wheels_utils_configure_wheels.assert_called_once_with(
            mocker.sentinel.player_controllers, mock_system, mocker.sentinel.metadata
        )
        get_generator.assert_called_once_with('default-emulator')

        assert call_external_scripts.call_args_list == [
            mocker.call(
                SYSTEM_SCRIPTS,
                'gameStart',
                ['system_name', 'default-emulator', 'default-core', Path('/var/squashfs/bar/bar.zip')],
            ),
            mocker.call(
                USER_SCRIPTS,
                'gameStart',
                ['system_name', 'default-emulator', 'default-core', Path('/var/squashfs/bar/bar.zip')],
            ),
            mocker.call(
                USER_SCRIPTS,
                'gameStop',
                ['system_name', 'default-emulator', 'default-core', Path('/var/squashfs/bar/bar.zip')],
            ),
            mocker.call(
                SYSTEM_SCRIPTS,
                'gameStop',
                ['system_name', 'default-emulator', 'default-core', Path('/var/squashfs/bar/bar.zip')],
            ),
        ]

        evmapy.assert_called_once_with(
            'system_name',
            'default-emulator',
            'default-core',
            ROMS / 'foo' / 'bar.squashfs',
            mocker.sentinel.new_player_controllers,
            mocker.sentinel.precalibrated_guns,
        )
        evmapy.return_value.__enter__.assert_called_once_with()
        set_hotkeygen_context.assert_called_once_with(generator, mock_system)
        set_hotkeygen_context.return_value.__enter__.assert_called_once_with()

        generator.executionDirectory.assert_called_once_with(mock_system.config, Path('/var/squashfs/bar/bar.zip'))
        generator.generate.assert_called_once_with(
            mock_system,
            Path('/var/squashfs/bar/bar.zip'),
            mocker.sentinel.new_player_controllers,
            mocker.sentinel.metadata,
            mocker.sentinel.precalibrated_guns,
            mocker.sentinel.wheels,
            {'width': 1920, 'height': 1080},
        )
        system_guns_borders_size_name.assert_called_once_with(mocker.sentinel.precalibrated_guns)
        system_guns_border_ratio_type.assert_called_once_with(mocker.sentinel.precalibrated_guns)
        get_hud_bezel.assert_called_once_with(
            mock_system,
            generator,
            Path('/var/squashfs/bar/bar.zip'),
            {'width': 1920, 'height': 1080},
            mocker.sentinel.guns_borders_size_name,
            mocker.sentinel.guns_border_ratio_type,
        )
        get_hud_config.assert_not_called()
        profiler.pause.return_value.__enter__.assert_called_once_with()
        run_command.assert_called_once_with(mock_command)
        profiler.pause.return_value.__exit__.assert_called_once_with(None, None, None)
        set_hotkeygen_context.return_value.__exit__.assert_called_once_with(None, None, None)
        evmapy.return_value.__exit__.assert_called_once_with(None, None, None)
        video_mode_change_mode.assert_not_called()
        video_mode_change_mouse.assert_not_called()
        wheels_utils_configure_wheels.return_value.__exit__.assert_called_once_with(None, None, None)

        assert Path(SAVES / 'system_name').is_dir()

    def test_password_not_in_log(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.DEBUG)

        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        mock_system.config['retroachievements.password'] = 'THIS IS MY PASSWORD'
        mock_system.config['netplay.password'] = 'THIS IS MY PASSWORD'

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        assert caplog.text.find("'retroachievements.password': '***'") > -1
        assert caplog.text.find("'netplay.password': '***'") > -1
        assert caplog.text.find('THIS IS MY PASSWORD') == -1

    def test_video_mode_change_from_es_to_max(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        video_mode_get_current_mode: Mock,
        video_mode_change_mode: Mock,
        video_mode_min_to_max_resolution: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        video_mode_get_current_mode.side_effect = ['1440x900.120.00', '1920x1080.60.00']

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        video_mode_min_to_max_resolution.assert_called_once_with()
        video_mode_change_mode.assert_called_once_with('1440x900.120.00')

    def test_video_mode_change_from_es_to_wanted(
        self,
        mocker: MockerFixture,
        mock_system: Emulator,
        default_args: Namespace,
        video_mode_get_current_mode: Mock,
        video_mode_change_mode: Mock,
        video_mode_min_to_max_resolution: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        mock_system.config['videomode'] = '640x480.120.00'
        video_mode_get_current_mode.return_value = '1440x900.120.00'

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        video_mode_min_to_max_resolution.assert_not_called()
        assert video_mode_change_mode.call_args_list == [mocker.call('640x480.120.00'), mocker.call('1440x900.120.00')]

    def test_video_mode_change_from_max_to_generator_default(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        video_mode_change_mode: Mock,
        video_mode_min_to_max_resolution: Mock,
        generator: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        generator.getResolutionMode.side_effect = ['default']

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        video_mode_min_to_max_resolution.assert_called_once_with()
        video_mode_change_mode.assert_not_called()

    def test_video_mode_change_from_es_to_generator_default_with_config(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
        video_mode_get_current_mode: Mock,
        video_mode_change_mode: Mock,
        video_mode_min_to_max_resolution: Mock,
        generator: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        video_mode_get_current_mode.return_value = '1440x900.120.00'
        mock_system.config['videomode'] = '640x480.120.00'
        generator.getResolutionMode.side_effect = ['default']

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        video_mode_min_to_max_resolution.assert_not_called()
        video_mode_change_mode.assert_not_called()

    def test_resolution_reversed(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
        video_mode_is_resolution_reversed: Mock,
        generator: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        video_mode_is_resolution_reversed.return_value = True

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        generator.generate.assert_called_once_with(
            mock_system,
            Path('/var/squashfs/bar/bar.zip'),
            mocker.sentinel.new_player_controllers,
            mocker.sentinel.metadata,
            mocker.sentinel.precalibrated_guns,
            mocker.sentinel.wheels,
            {'width': 1080, 'height': 1920},
        )

    @pytest.mark.parametrize(
        ('value', 'expected'),
        [
            (True, '1'),
            (False, '0'),
        ],
    )
    def test_sdlvsync(
        self, mocker: MockerFixture, default_args: Namespace, mock_system: Emulator, value: bool, expected: str
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        mock_system.config['sdlvsync'] = value

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        assert mock_system.config['sdlvsync'] == expected
        assert os.environ['SDL_RENDER_VSYNC'] == expected

    def test_mouse_mode(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        generator: Mock,
        video_mode_change_mouse: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        generator.getMouseMode.return_value = True

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        assert video_mode_change_mouse.call_args_list == [mocker.call(True), mocker.call(False)]

    def test_execution_directory(
        self,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        default_args: Namespace,
        generator: Mock,
    ) -> None:
        fs.create_dir('/path/to/emulator')
        assert fs.cwd != '/path/to/emulator'

        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        generator.executionDirectory.return_value = '/path/to/emulator'

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        assert fs.cwd == '/path/to/emulator'

    def test_no_hud_support(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        get_hud_bezel = mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        mock_system.config['hud_support'] = '0'

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        get_hud_bezel.assert_not_called()

    @pytest.mark.parametrize('value', ['', 'none'])
    def test_no_hud_config(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
        value: str,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)
        get_hud_config = mocker.patch('configgen.emulatorlauncher.getHudConfig')

        mock_system.config['hud'] = value

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        get_hud_config.assert_not_called()

    @pytest.mark.parametrize('has_internal_call', [True, False])
    @pytest.mark.parametrize('bezel_is_not_none', [True, False])
    def test_hud_config(
        self,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        default_args: Namespace,
        mock_system: Emulator,
        mock_command: Command,
        bezel_is_not_none: bool,
        has_internal_call: bool,
        generator: Mock,
    ) -> None:
        fs.create_dir('/var/run')

        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch(
            'configgen.emulatorlauncher.getHudBezel',
            return_value=mocker.sentinel.hud_bezel if bezel_is_not_none else None,
        )
        get_hud_config = mocker.patch('configgen.emulatorlauncher.getHudConfig', return_value='hud config')

        mock_system.config['hud'] = 'none' if bezel_is_not_none else 'custom'

        mock_command.array = ['1', '2', '3', Path('/foo')]
        default_args.gameinfoxml = mocker.sentinel.gameinfoxml
        default_args.systemname = mocker.sentinel.systemname

        generator.hasInternalMangoHUDCall.return_value = has_internal_call

        assert (
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )
            == mocker.sentinel.run_command
        )

        get_hud_config.assert_called_once_with(
            mock_system,
            mocker.sentinel.systemname,
            'default-emulator',
            'default-core',
            Path('/var/squashfs/bar/bar.zip'),
            mocker.sentinel.hud_bezel if bezel_is_not_none else None,
        )
        assert mock_command.env == {
            'MANGOHUD_DLSYM': '1',
            'MANGOHUD_CONFIGFILE': Path('/var/run/hud.config'),
        }

        assert mock_command.array[0] == '1' if has_internal_call else 'mangohud'
        assert Path('/var/run/hud.config').read_text() == 'hud config'

    def test_cleanup(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        generator: Mock,
        mock_system: Emulator,
        video_mode_get_current_mode: Mock,
        video_mode_change_mode: Mock,
        video_mode_change_mouse: Mock,
        wheels_utils_configure_wheels: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        test_exception = Exception('Test exception')
        mock_system.config['use_wheels'] = '1'
        mock_system.config['videomode'] = '640x480.120.00'
        video_mode_get_current_mode.return_value = '1440x900.120.00'
        generator.getMouseMode.return_value = True
        generator.generate.side_effect = test_exception

        with pytest.raises(Exception, match=r'^Test exception$'):
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )

        assert video_mode_change_mode.call_args_list == [mocker.call('640x480.120.00'), mocker.call('1440x900.120.00')]
        assert video_mode_change_mouse.call_args_list == [mocker.call(True), mocker.call(False)]
        wheels_utils_configure_wheels.return_value.__exit__.assert_called_once_with(
            Exception, test_exception, mocker.ANY
        )

    @pytest.mark.parametrize(
        'raising_fixture',
        [lf('video_mode_change_mode'), lf('video_mode_change_mouse')],
    )
    def test_cleanup_raises(
        self,
        mocker: MockerFixture,
        default_args: Namespace,
        generator: Mock,
        mock_system: Emulator,
        video_mode_get_current_mode: Mock,
        video_mode_change_mode: Mock,
        video_mode_change_mouse: Mock,
        wheels_utils_configure_wheels: Mock,
        raising_fixture: Mock,
    ) -> None:
        from configgen.emulatorlauncher import start_rom

        mocker.patch('configgen.emulatorlauncher.callExternalScripts')
        mocker.patch('configgen.emulatorlauncher.runCommand', return_value=mocker.sentinel.run_command)
        mocker.patch('configgen.emulatorlauncher.getHudBezel', return_value=None)

        test_exception = Exception('Test exception')

        mock_system.config['use_wheels'] = '1'
        mock_system.config['videomode'] = '640x480.120.00'
        video_mode_get_current_mode.return_value = '1440x900.120.00'
        generator.getMouseMode.return_value = True
        generator.generate.side_effect = test_exception

        raising_fixture.side_effect = [None, Exception('Cleanup exception')]

        with pytest.raises(Exception, match=r'^Test exception$'):
            start_rom(
                default_args,
                8,
                Path('/var/squashfs/bar/bar.zip'),
                ROMS / 'foo' / 'bar.squashfs',
            )

        assert video_mode_change_mode.call_args_list == [mocker.call('640x480.120.00'), mocker.call('1440x900.120.00')]
        assert video_mode_change_mouse.call_args_list == [mocker.call(True), mocker.call(False)]
        wheels_utils_configure_wheels.return_value.__exit__.assert_called_once_with(
            Exception, test_exception, mocker.ANY
        )
