from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.ppsspp.ppssppGenerator import PPSSPPGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


@pytest.mark.usefixtures('fs')
class TestPPSSPPGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[PPSSPPGenerator]:
        return PPSSPPGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'psp'

    @pytest.fixture
    def emulator(self) -> str:
        return 'ppsspp'

    def test_get_mouse_mode(self, generator: PPSSPPGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: PPSSPPGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: PPSSPPGenerator,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'psp' / 'rom.chd',
                two_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'ppsspp.ini').read_text() == snapshot(name='config')
        assert (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'controls.ini').read_text() == snapshot(name='controls')

    def test_generate_existing(
        self,
        generator: PPSSPPGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'ppsspp' / 'gamecontrollerdb.txt')
        fs.create_file(
            CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'ppsspp.ini',
            contents="""[Graphics]
ShowFPSCounter = 1

[SystemParam]
NickName = Blah

[General]
RewindFlipFrequency = 1

[Upgrade]
UpgradeMessage = asdf
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'psp' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert not (CONFIGS / 'ppsspp' / 'gamecontrollerdb.txt').exists()
        assert (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'ppsspp.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'state_filename': '/userdata/saves/ppsspp/0.state'},
            {'state_slot': '4'},
            {'showFPS': '1'},
            {'frameskip': '2'},
            {'frameskip': 'automatic', 'skip_buffer_effects': 'False'},
            {'skip_buffer_effects': 'True', 'internal_resolution': '2'},
            {'internal_resolution': '2'},
            {'skip_buffer_effects': 'True', 'autoframeskip': '0'},
            {'skip_buffer_effects': 'True', 'autoframeskip': '1'},
            {'autoframeskip': '0'},
            {'autoframeskip': '1'},
            {'vsyncinterval': '0'},
            {'vsyncinterval': '1'},
            {'display_integer_scale': 'False'},
            {'display_integer_scale': 'True'},
            {'texture_scaling_level': '2'},
            {'texture_scaling_type': '1'},
            {'texture_deposterize': 'False'},
            {'anisotropic_filtering': '1'},
            {'texture_filtering': '2'},
            {'retroachievements': '1', 'retroachievements.username': 'foobarbaz'},
            {'rewind': '0'},
            {'rewind': '1'},
            {'enable_cheats': 'True'},
            {'ppsspp.Foo.Bar': 'Baz', 'ppsspp.General.EnableCheats': 'True'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: PPSSPPGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'psp' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'ppsspp.ini').read_text() == snapshot(name='config')

    @pytest.mark.mock_system_config({'gfxbackend': '3 (VULKAN)'})
    @pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name')
    @pytest.mark.parametrize(
        ('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_name'),
        [
            pytest.param(False, False, None, id='vulkan not available'),
            pytest.param(True, False, None, id='vulkan available, no discrete gpu'),
            pytest.param(True, True, None, id='vulkan available, unable to get gpu name'),
            pytest.param(True, True, 'discrete1', id='vulkan available'),
        ],
        indirect=True,
    )
    def test_generate_vulkan(
        self,
        generator: PPSSPPGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psp' / 'rom.chd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'ppsspp.ini').read_text() == snapshot

    @pytest.mark.parametrize('resolution', [{'width': 640, 'height': 480}, {'width': 480, 'height': 640}], ids=str)
    def test_generate_low_res(
        self,
        generator: PPSSPPGenerator,
        mock_system: Emulator,
        resolution: Resolution,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'psp' / 'rom.chd',
                one_player_controllers,
                {},
                [],
                {},
                resolution,
            )
            == snapshot
        )

    def test_generate_no_player_1(self, generator: PPSSPPGenerator, mock_system: Emulator) -> None:
        generator.generate(
            mock_system,
            ROMS / 'psp' / 'rom.chd',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert not (CONFIGS / 'ppsspp' / 'PSP' / 'SYSTEM' / 'controls.ini').exists()
