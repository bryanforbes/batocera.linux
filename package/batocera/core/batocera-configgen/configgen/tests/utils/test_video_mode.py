from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Any
from unittest.mock import call

import pytest

from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.utils.videoMode import (
    changeMode,
    changeMouse,
    checkModeExists,
    getAltDecoration,
    getCurrentMode,
    getCurrentOutput,
    getCurrentResolution,
    getGLVendor,
    getGLVersion,
    getRefreshRate,
    getScreens,
    getScreensInfos,
    isResolutionReversed,
    minTomaxResolution,
    supportSystemRotation,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.types import Resolution, ScreenInfo


@pytest.fixture
def check_mode_exists(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.videoMode.checkModeExists')


def test_change_mode(subprocess_run: Mock, check_mode_exists: Mock) -> None:
    check_mode_exists.return_value = True

    changeMode('1920x1080.120.0')

    subprocess_run.assert_called_once_with(
        ['batocera-resolution', 'setMode', '1920x1080.120.0'], capture_output=True, text=True, check=True
    )


def test_change_mode_check_fails(subprocess_run: Mock, check_mode_exists: Mock) -> None:
    check_mode_exists.return_value = False

    changeMode('1920x1080.120.0')

    subprocess_run.assert_not_called()


def test_change_mode_first_fails(mocker: MockerFixture, subprocess_run: Mock, check_mode_exists: Mock) -> None:
    check_mode_exists.return_value = True

    subprocess_run.side_effect = [
        subprocess.CalledProcessError(1, ['batocera-resolution', 'setMode', '1920x1080.120.0']),
        mocker.Mock(),
    ]

    changeMode('1920x1080.120.0')

    assert subprocess_run.call_args_list == [
        call(['batocera-resolution', 'setMode', '1920x1080.120.0'], capture_output=True, text=True, check=True),
        call(['batocera-resolution', 'setMode', '1920x1080.120.0'], capture_output=True, text=True, check=True),
    ]


def test_change_mode_fails(subprocess_run: Mock, check_mode_exists: Mock) -> None:
    check_mode_exists.return_value = True

    subprocess_run.side_effect = subprocess.CalledProcessError(1, ['batocera-resolution', 'setMode', '1920x1080.120.0'])

    with pytest.raises(BatoceraException, match=r'^Error setting video mode$'):
        changeMode('1920x1080.120.0')


def test_get_current_mode(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (
        b"""1920x1080.120.00
1024x768.120.00
""",
        b'',
    )
    subprocess_popen.return_value = popen_instance

    assert getCurrentMode() == '1920x1080.120.00'
    subprocess_popen.assert_called_once_with(['batocera-resolution currentMode'], stdout=subprocess.PIPE, shell=True)


def test_get_current_mode_none(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'', b'')
    subprocess_popen.return_value = popen_instance

    assert getCurrentMode() is None
    subprocess_popen.assert_called_once_with(['batocera-resolution currentMode'], stdout=subprocess.PIPE, shell=True)


def test_get_refresh_rate(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (
        b"""120.00
60.00
""",
        b'',
    )
    subprocess_popen.return_value = popen_instance

    assert getRefreshRate() == '120.00'
    subprocess_popen.assert_called_once_with(['batocera-resolution refreshRate'], stdout=subprocess.PIPE, shell=True)


def test_get_refresh_rate_none(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'', b'')
    subprocess_popen.return_value = popen_instance

    assert getRefreshRate() is None
    subprocess_popen.assert_called_once_with(['batocera-resolution refreshRate'], stdout=subprocess.PIPE, shell=True)


@pytest.mark.parametrize(
    ('screens', 'output', 'resolutions', 'config', 'expected', 'expected_calls'),
    [
        pytest.param(
            ['screen1'],
            'screen1',
            [{'width': 1920, 'height': 1080}],
            {},
            [{'width': 1920, 'height': 1080, 'x': 0, 'y': 0}],
            [call()],
            id='one screen',
        ),
        pytest.param(
            ['screen1', 'screen2'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}],
            {},
            [{'width': 640, 'height': 480, 'x': 0, 'y': 0}, {'width': 1920, 'height': 1080, 'x': 640, 'y': 0}],
            [call(), call('screen1')],
            id='two screens',
        ),
        pytest.param(
            ['screen1', 'screen2'],
            'screen2',
            [{'width': 640, 'height': 480}, Exception],
            {},
            [{'width': 640, 'height': 480, 'x': 0, 'y': 0}],
            [call(), call('screen1')],
            id='two screens, screen1 resolution raises',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3'],
            'screen3',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen1'), call('screen2')],
            id='three screens',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3'],
            'screen3',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, Exception],
            {},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
            ],
            [call(), call('screen1'), call('screen2')],
            id='three screens, screen2 resolution raises',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput2': 'screen3'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen3'), call('screen1')],
            id='three screens, videooutput2 set to screen3',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput2': 'screen2'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen1'), call('screen3')],
            id='three screens, videooutput2 set to output 1',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput2': 'screen4'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen1'), call('screen3')],
            id='three screens, videooutput2 set to screen4',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3', 'screen4'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput3': 'screen4'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen1'), call('screen4')],
            id='four screens, videooutput3 set to screen4',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3', 'screen4'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput3': 'screen1'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen1'), call('screen3')],
            id='four screens, videooutput3 set to screen1',
        ),
        pytest.param(
            ['screen1', 'screen2', 'screen3', 'screen4'],
            'screen2',
            [{'width': 640, 'height': 480}, {'width': 1920, 'height': 1080}, {'width': 1024, 'height': 768}],
            {'videooutput2': 'screen3', 'videooutput3': 'screen1'},
            [
                {'width': 640, 'height': 480, 'x': 0, 'y': 0},
                {'width': 1920, 'height': 1080, 'x': 640, 'y': 0},
                {'width': 1024, 'height': 768, 'x': 2560, 'y': 0},
            ],
            [call(), call('screen3'), call('screen1')],
            id='four screens, videooutput2 set to screen3, videooutput3 set to screen1',
        ),
    ],
)
def test_get_screens_infos(
    mocker: MockerFixture,
    screens: list[str],
    output: str,
    resolutions: list[Resolution | type[Exception]],
    config: dict[str, str],
    expected: list[ScreenInfo],
    expected_calls: list[Any],
) -> None:
    mocker.patch('configgen.utils.videoMode.getScreens', return_value=screens)
    mocker.patch('configgen.utils.videoMode.getCurrentOutput', return_value=output)
    get_current_resolution = mocker.patch('configgen.utils.videoMode.getCurrentResolution', side_effect=resolutions)

    assert getScreensInfos(SystemConfig(config)) == expected
    assert get_current_resolution.call_args_list == expected_calls


def test_get_screens(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (
        b"""foo
bar
""",
        b'',
    )
    subprocess_popen.return_value = popen_instance

    assert getScreens() == ['foo', 'bar']
    subprocess_popen.assert_called_once_with(['batocera-resolution listOutputs'], stdout=subprocess.PIPE, shell=True)


def test_min_to_max_resolution(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'', b'')
    subprocess_popen.return_value = popen_instance

    minTomaxResolution()

    subprocess_popen.assert_called_once_with(
        ['batocera-resolution minTomaxResolution'], stdout=subprocess.PIPE, shell=True
    )
    popen_instance.communicate.assert_called_once_with()


def test_get_current_resolution(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'1920x1080\n', b'')
    subprocess_popen.return_value = popen_instance

    assert getCurrentResolution() == {'width': 1920, 'height': 1080}
    subprocess_popen.assert_called_once_with(
        ['batocera-resolution currentResolution'], stdout=subprocess.PIPE, shell=True
    )


def test_get_current_resolution_for_screen(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'640x480\n', b'')
    subprocess_popen.return_value = popen_instance

    assert getCurrentResolution('screen_one') == {'width': 640, 'height': 480}
    subprocess_popen.assert_called_once_with(
        ['batocera-resolution --screen screen_one currentResolution'], stdout=subprocess.PIPE, shell=True
    )


def test_get_current_output(mocker: MockerFixture, subprocess_popen: Mock) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (
        b' \t \n screen_one \t \r   \n',
        b'',
    )
    subprocess_popen.return_value = popen_instance

    assert getCurrentOutput() == 'screen_one'
    subprocess_popen.assert_called_once_with(['batocera-resolution currentOutput'], stdout=subprocess.PIPE, shell=True)


@pytest.mark.parametrize(('returncode', 'expected'), [(0, True), (1, False)])
def test_support_system_rotation(
    mocker: MockerFixture, subprocess_popen: Mock, returncode: int, expected: bool
) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'', b'')
    popen_instance.returncode = returncode
    subprocess_popen.return_value = popen_instance

    assert supportSystemRotation() == expected
    subprocess_popen.assert_called_once_with(
        ['batocera-resolution supportSystemRotation'], stdout=subprocess.PIPE, shell=True
    )
    popen_instance.communicate.assert_called_once_with()


@pytest.mark.parametrize('expected', [True, False])
def test_is_resolution_reversed(fs: FakeFilesystem, expected: bool) -> None:
    if expected:
        fs.create_file('/var/run/rk-rotation')

    assert isResolutionReversed() == expected


@pytest.mark.parametrize(
    ('mode', 'expected'),
    [
        ('max-1920x1080', True),
        ('1920x1080.120.00', True),
        ('640x480.60.00', False),
        ('max-foo', False),
    ],
)
def test_check_mode_exists(
    mocker: MockerFixture, subprocess_popen: Mock, mode: str, expected: bool, snapshot: SnapshotAssertion
) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (
        b"""max-1920x1080:maximum 1920x1080
1920x1080.120.00:1920x1080 120.00 Hz
1024x768.120.00:1024x768 120.00 Hz
640x480.120.00:640x480 120.00 Hz
""",
        b'',
    )
    subprocess_popen.return_value = popen_instance

    assert checkModeExists(mode) == expected
    assert subprocess_popen.call_args_list == snapshot


@pytest.mark.parametrize(('mode', 'expected'), [(True, 'show'), (False, 'hide')])
def test_change_mouse(mocker: MockerFixture, subprocess_popen: Mock, mode: bool, expected: str) -> None:
    popen_instance = mocker.Mock()
    popen_instance.communicate.return_value = (b'', b'')
    subprocess_popen.return_value = popen_instance

    changeMouse(mode)
    subprocess_popen.assert_called_once_with([f'batocera-mouse {expected}'], stdout=subprocess.PIPE, shell=True)
    popen_instance.communicate.assert_called_once_with()


@pytest.mark.parametrize(('version', 'expected'), [('4.6', 4.6), ('3.2.3.0', 3.2)])
def test_get_gl_version(fs: FakeFilesystem, mocker: MockerFixture, version: str, expected: float) -> None:
    fs.create_file('/usr/bin/glxinfo')

    check_output = mocker.patch(
        'subprocess.check_output',
        return_value=b'OpenGL version string: ' + version.encode('utf-8') + b' (Compatibility Profile) Mesa 24.3.3',
    )

    assert getGLVersion() == expected
    check_output.assert_called_once_with('glxinfo | grep "OpenGL version"', shell=True)


def test_get_gl_version_no_glxinfo(mocker: MockerFixture) -> None:
    check_output = mocker.patch('subprocess.check_output', return_value=b'')

    assert getGLVersion() == 0
    check_output.assert_not_called()


def test_get_gl_version_exception(fs: FakeFilesystem, mocker: MockerFixture) -> None:
    fs.create_file('/usr/bin/glxinfo')
    mocker.patch('subprocess.check_output', side_effect=Exception)

    assert getGLVersion() == 0


def test_get_gl_vendor(fs: FakeFilesystem, mocker: MockerFixture) -> None:
    fs.create_file('/usr/bin/glxinfo')

    check_output = mocker.patch(
        'subprocess.check_output',
        return_value=b'OpenGL vendor string: AmD',
    )

    assert getGLVendor() == 'amd'
    check_output.assert_called_once_with('glxinfo | grep "OpenGL vendor string"', shell=True)


def test_get_gl_vendor_no_glxinfo(mocker: MockerFixture) -> None:
    check_output = mocker.patch('subprocess.check_output', return_value=b'')

    assert getGLVendor() == 'unknown'
    check_output.assert_not_called()


def test_get_gl_vendor_exception(fs: FakeFilesystem, mocker: MockerFixture) -> None:
    fs.create_file('/usr/bin/glxinfo')
    mocker.patch('subprocess.check_output', side_effect=Exception)

    assert getGLVendor() == 'unknown'


@pytest.mark.parametrize('emulator', ['flycast', 'mame', 'retroarch'])
@pytest.mark.parametrize('system', ['dreamcast', 'naomi'])
def test_get_alt_decoration(system: str, emulator: str) -> None:
    assert getAltDecoration(system, '/path/to/rom.zip', emulator) == ('standalone' if emulator == 'flycast' else '0')


@pytest.mark.parametrize('emulator', ['mame', 'retroarch'])
@pytest.mark.parametrize(
    'system', ['lynx', 'wswan', 'wswanc', 'mame', 'fbneo', 'naomi', 'atomiswave', 'nds', '3ds', 'vectrex']
)
def test_get_alt_decoration_special_file(fs: FakeFilesystem, system: str, emulator: str) -> None:
    fs.create_file(
        f'/usr/share/batocera/configgen/data/special/{system}.csv',
        contents="""foo - bar;270
rOm;90
baz blah ham (Spam);180
""",
    )

    assert getAltDecoration(system, '/path/to/RoM.zip', emulator) == '90'


@pytest.mark.parametrize('emulator', ['mame', 'retroarch'])
@pytest.mark.parametrize(
    'system', ['lynx', 'wswan', 'wswanc', 'mame', 'fbneo', 'naomi', 'atomiswave', 'nds', '3ds', 'vectrex']
)
def test_get_alt_decoration_special_file_not_found(fs: FakeFilesystem, system: str, emulator: str) -> None:
    fs.create_file(
        f'/usr/share/batocera/configgen/data/special/{system}.csv',
        contents="""foo - bar;270
baz blah ham (Spam);180
""",
    )

    assert getAltDecoration(system, '/path/to/RoM.zip', emulator) == '0'
