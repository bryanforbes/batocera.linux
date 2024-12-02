from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.ioquake3.ioquake3Generator import IOQuake3Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


class TestIOQuake3Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[IOQuake3Generator]:
        return IOQuake3Generator

    @pytest.fixture
    def system_name(self) -> str:
        return 'quake3'

    @pytest.fixture
    def emulator(self) -> str:
        return 'ioquake3'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/ioquake3/ioquake3', contents='ioquake3 bin')
        return fs

    @pytest.mark.parametrize(
        ('resolution', 'result'),
        [
            ({'width': 640, 'height': 480}, 4 / 3),
            ({'width': 1920, 'height': 1080}, 16 / 9),
            ({'width': 1920, 'height': 1144}, 16 / 9),
            ({'width': 1920, 'height': 1145}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: IOQuake3Generator, resolution: Resolution, result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig({}), resolution, Path()) == result

    @pytest.mark.parametrize('core', ['ioquake3', 'vkquake3'])
    def test_generate(
        self,
        generator: IOQuake3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'quake3' / 'baseq3')
        fs.create_dir(ROMS / 'quake3' / 'missionpack')
        fs.create_file(ROMS / 'quake3' / 'Quake III Arena.quake3', contents='+set fs_game "baseq3"\nsome stuff\n')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'quake3' / 'Quake III Arena.quake3',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert filecmp.cmp('/usr/bin/ioquake3/ioquake3', ROMS / 'quake3' / 'ioquake3')
        assert (CONFIGS / 'ioquake3' / 'baseq3' / 'q3config.cfg').read_text() == snapshot(name='baseq3 config')
        assert (CONFIGS / 'ioquake3' / 'missionpack' / 'q3config.cfg').read_text() == snapshot(
            name='missionpack config'
        )

    @pytest.mark.parametrize(
        ('core', 'mock_system_config'),
        [
            ('ioquake3', {'ioquake3_mem': '64'}),
            ('vkquake3', {'ioquake3_mem': '64'}),
            ('vkquake3', {'vkquake3_api': 'opengl2'}),
            ('vkquake3', {'vkquake3_api': 'vulkan'}),
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: IOQuake3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'quake3' / 'baseq3')
        fs.create_file(ROMS / 'quake3' / 'Quake III Arena.quake3')

        generator.generate(
            mock_system,
            ROMS / 'quake3' / 'Quake III Arena.quake3',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'ioquake3' / 'baseq3' / 'q3config.cfg').read_text() == snapshot

    @pytest.mark.parametrize(
        ('core', 'mock_system_config'),
        [
            ('ioquake3', {}),
            ('ioquake3', {'ioquake3_mem': '64'}),
            ('vkquake3', {}),
            ('vkquake3', {'ioquake3_mem': '64'}),
            ('vkquake3', {'vkquake3_api': 'opengl2'}),
            ('vkquake3', {'vkquake3_api': 'vulkan'}),
        ],
        ids=str,
    )
    def test_generate_existing(
        self,
        generator: IOQuake3Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'quake3' / 'ioquake3', contents='new ioquake3 bin')
        fs.create_dir(ROMS / 'quake3' / 'baseq3')
        fs.create_file(ROMS / 'quake3' / 'Quake III Arena.quake3')
        fs.create_file(
            CONFIGS / 'ioquake3' / 'baseq3' / 'q3config.cfg',
            contents="""seta r_mode "-1"
seta r_customwidth "640"
seta r_customheight "480"
seta in_joystickUseAnalog "0"
seta in_joystick "0"
seta cl_allowDownload "0"
seta com_hunkMegs "64"
seta cl_renderer "foo"
bind PAD0_LEFTSHOULDER "weapnext"
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'quake3' / 'Quake III Arena.quake3',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'quake3' / 'ioquake3').read_text() == 'new ioquake3 bin'
        assert (CONFIGS / 'ioquake3' / 'baseq3' / 'q3config.cfg').read_text() == snapshot(name='baseq3 config')
