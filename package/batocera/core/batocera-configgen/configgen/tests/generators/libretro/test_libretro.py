from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ES_SETTINGS, OVERLAYS, ROMS
from configgen.exceptions import MissingCore
from configgen.generators.libretro.libretroConfig import connected_to_internet
from tests.generators.base import GeneratorBaseTest
from tests.generators.libretro.base import LibretroBaseMixin
from tests.generators.libretro.utils import (
    get_configs,
    get_configs_from_bases,
    get_configs_with_base,
    get_configs_with_bases,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator
    from configgen.types import Resolution

pytestmark = pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index')


@pytest.mark.parametrize(
    ('returncodes', 'expected'),
    [
        pytest.param([0], True, id='connected, one try'),
        pytest.param([1, 0], True, id='connected, two tries'),
        pytest.param([1, 1, 0], False, id='not connected'),
    ],
)
def test_connected_to_internet(
    mocker: MockerFixture,
    subprocess_popen: Mock,
    returncodes: list[int],
    expected: bool,
    snapshot: SnapshotAssertion,
) -> None:
    subprocess_popen.side_effect = [mocker.Mock(returncode=code) for code in returncodes]

    assert connected_to_internet() == expected
    assert subprocess_popen.call_args_list == snapshot


class TestLibretroGenerator(GeneratorBaseTest, LibretroBaseMixin):
    @pytest.fixture
    def system_name(self) -> str:
        return '__UNKNOWN_SYSTEM__'

    @pytest.fixture
    def core(self) -> str:
        return '__UNKNOWN_CORE__'

    @pytest.fixture
    def video_mode_support_system_rotation(self, mocker: MockerFixture, request: SubRequest) -> Mock:
        return mocker.patch('configgen.utils.videoMode.supportSystemRotation', return_value=request.param)

    def test_supports_internal_bezels(self, generator: Generator) -> None:
        assert generator.supportsInternalBezels()

    @pytest.mark.mock_system_config({'configfile': '/path/to/my/config.cfg'})
    def test_generate_configfile(
        self,
        generator: Generator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.smc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert not (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').exists()
        assert not (CONFIGS / 'retroarch' / 'config' / 'remaps' / 'common' / 'common.rmp').exists()
        assert not (CONFIGS / 'retroarch' / 'cores' / 'retroarch-core-options.cfg').exists()

    def test_generate_missing_info(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.zip')
        shutil.rmtree('/usr/share/libretro/info')

        with pytest.raises(MissingCore):
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    def test_generate_custom_game_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.smc')
        fs.create_file(CONFIGS / 'retroarch' / mock_system.name / 'rom.smc.cfg')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.smc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_overlay_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / 'rom.smc')
        fs.create_file(OVERLAYS / mock_system.name / 'rom.smc.cfg')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.smc',
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
            {'state_slot': '3', 'state_filename': 'statefilename.state'},
            {'state_slot': '3', 'state_filename': 'statefilename.auto'},
            {'retroarchcore.foo': 'bar'},
            {'retroarch.foo': 'bar'},
            {'audio_driver': 'alsa'},
            {'audio_latency': '256'},
            {'audio_volume': '2.000000'},
            *get_configs('video_threaded', ['1', '0']),
            *get_configs('video_allow_rotate', ['true', 'false']),
            *get_configs('vrr_runloop_enable', ['1', '0']),
            *get_configs('smooth', ['1', '0']),
            *get_configs('video_frame_delay_auto', ['1', '0']),
            *get_configs('autosave', ['1', '0']),
            *get_configs('integerscale', ['1', '0']),
            *get_configs('showFPS', ['1', '0']),
            *get_configs_with_base(
                {'ai_service_enabled': '1'},
                [('ai_target_lang', 'Fr'), ('ai_service_url', 'https://some.ai/url'), ('ai_service_pause', ['0', '1'])],
            ),
            *get_configs('incrementalsavestates', ['0', '1', '2']),
            *get_configs('retroachievements.sound', ['none', 'woohoo.wav']),
            {'system.language': 'ja_JP'},
            {'retroarch.user_language': '1', 'system.language': 'ko_KR'},
            {'system.language': 'ko_KR'},
            {'retroarch.user_language': '10', 'system.language': 'zh_TW'},
            {'system.language': 'zh_TW'},
            {'retroarch.user_language': '11', 'system.language': 'zh_CN'},
            {'system.language': 'zh_CN'},
            {'retroarch.user_language': '12', 'system.language': 'ja_JP'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'unknown' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        'video_mode_support_system_rotation', [True, False], indirect=True, ids=['supports rotation', 'no rotation']
    )
    @pytest.mark.parametrize(
        'mock_system_config',
        [*get_configs('display.rotate', ['0', '1', '2', '3'])],
        ids=str,
    )
    @pytest.mark.usefixtures('video_mode_support_system_rotation')
    def test_generate_config_display_rotate(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        generator.generate(
            mock_system,
            ROMS / 'unknown' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        ('ratio', 'autowidescreen', 'get_games_metadata'),
        [
            ('16/9', None, None),
            ('auto', None, None),
            ('auto', 'False', None),
            ('auto', 'True', None),
            pytest.param('auto', 'True', {'video_widescreen': 'false'}, id='auto-True-false'),
            pytest.param('auto', 'True', {'video_widescreen': 'true'}, id='auto-True-true'),
        ],
        indirect=['get_games_metadata'],
        ids=str,
    )
    @pytest.mark.usefixtures('get_games_metadata')
    def test_generate_config_ratio(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        ratio: str,
        autowidescreen: bool | None,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        mock_system.config['ratio'] = ratio
        if autowidescreen is not None:
            mock_system.config[f'{mock_system.config["core"]}-autowidescreen'] = str(autowidescreen)

        generator.generate(
            mock_system,
            ROMS / 'unknown' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize('resolution', [{'width': 479, 'height': 1080}, {'width': 1920, 'height': 479}], ids=str)
    def test_generate_low_resolution(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        resolution: Resolution,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        generator.generate(
            mock_system,
            ROMS / 'unknown' / 'rom.zip',
            [],
            {},
            [],
            {},
            resolution,
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize('value', ['true', 'false', 'foo', None])
    def test_generate_invert_buttons(
        self,
        generator: Generator,
        value: str | None,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ES_SETTINGS,
            contents=f"""<?xml version="1.0"?>
<config>
\t<bool name="DrawFramerate" value="true" />
{f'\t<bool name="InvertButtons" value="{value}" />' if value is not None else ''}
</config>
""",
        )

        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        generator.generate(
            mock_system,
            ROMS / 'unknown' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.mock_system_config({'gfxbackend': 'vulkan'})
    @pytest.mark.parametrize(
        ('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index'),
        [
            pytest.param(False, False, None, id='vulkan unavailable'),
            pytest.param(True, False, None, id='vulkan available, no discrete gpu'),
            pytest.param(True, True, None, id='vulkan available, unable to get gpu index'),
            pytest.param(True, True, '42', id='vulkan available'),
        ],
        indirect=True,
    )
    def test_generate_vulkan(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        generator.generate(
            mock_system,
            ROMS / 'unknown' / 'rom.zip',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'netplay.mode': 'foo'},
            *get_configs_with_base(
                {'netplay.mode': 'host'},
                [
                    ('netplay.nickname', 'host_nick'),
                    ('netplay_public_announce', ['0', '1']),
                ],
            ),
            *get_configs_with_base(
                {'netplay.mode': 'client', 'netplay.server.ip': '1.1.1.1'},
                [
                    ('netplay.server.port', '111'),
                    ('netplay.server.session', 'client_session_id'),
                    ('netplay.nickname', 'client_nick'),
                    ('netplay.password', 'client_pass'),
                ],
            ),
            *get_configs_with_base(
                {'netplay.mode': 'spectator', 'netplay.server.ip': '2.2.2.2'},
                [
                    ('netplay.server.port', '222'),
                    ('netplay.server.session', 'spectator_session_id'),
                    ('netplay.nickname', 'spectator_nick'),
                    ('netplay.password', 'spectator_pass'),
                ],
            ),
            *get_configs_with_bases(
                get_configs_from_bases(
                    [
                        {'netplay.mode': 'host'},
                        {'netplay.mode': 'client', 'netplay.server.ip': '1.1.1.1'},
                        {'netplay.mode': 'spectator', 'netplay.server.ip': '2.2.2.2'},
                    ],
                    [
                        ('netplay.relay', ['', 'none', 'nyc', 'madrid', 'montreal', 'saopaulo', 'custom']),
                    ],
                ),
                [
                    ('netplay.customserver', 'https://customserver.com'),
                ],
            ),
        ],
        ids=str,
    )
    def test_generate_netplay(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'unknown' / 'rom.zip')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'unknown' / 'rom.zip',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        self.assert_config_matches(snapshot)
