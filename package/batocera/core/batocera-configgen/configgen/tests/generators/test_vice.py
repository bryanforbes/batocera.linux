from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.vice.viceGenerator import ViceGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator
    from configgen.gun import Guns


@pytest.mark.usefixtures('fs')
class TestViceGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ViceGenerator]:
        return ViceGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'c64'

    @pytest.fixture
    def emulator(self) -> str:
        return 'vice'

    @pytest.fixture
    def core(self) -> str:
        return 'x64'

    def test_get_resolution_mode(self, generator: ViceGenerator) -> None:  # pyright: ignore
        assert generator.getResolutionMode(SystemConfig({})) == 'default'

    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate(
        self,
        generator: ViceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'c64' / 'rom.d64',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')
        assert (CONFIGS / 'vice' / 'sdl-joymap.vjm').read_text() == snapshot(name='joymap')

    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate_existing(
        self,
        generator: ViceGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'vice' / 'sdl-vicerc',
            contents="""[C64]
SaveResourcesOnExit=1

[PLUS4]
SaveResourcesOnExit=1

[SCPU64]
SaveResourcesOnExit=1

[VIC20]
SaveResourcesOnExit=1

[PET]
SaveResourcesOnExit=1

[C128]
SaveResourcesOnExit=1
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'c64' / 'rom.d64',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')

    @pytest.mark.mock_system_config({'noborder': '1'})
    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate_noborder(
        self,
        generator: ViceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'c64' / 'rom.d64',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')

    @pytest.mark.mock_system_config({'use_guns': '1'})
    @pytest.mark.parametrize(
        ('guns', 'metadata'),
        [
            pytest.param([], {}, id='no guns, no metadata'),
            pytest.param([{}], {'gun_type': 'foo'}, id='one gun, gun_type=foo'),
            pytest.param([{}], {'gun_type': 'stack_light_rifle'}, id='one gun, gun_type=stack_light_rifle'),
            pytest.param([], {'gun_type': 'stack_light_rifle'}, id='no guns, gun_type=stack_light_rifle'),
        ],
    )
    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate_guns(
        self,
        generator: ViceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        guns: Guns,
        metadata: dict[str, Any],
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'c64' / 'rom.d64',
            one_player_controllers,
            metadata,
            guns,
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')

    @pytest.mark.mock_system_config(
        {
            'vice.C64.SomeOption': 'value',
            'vice.Blah.SomeOtherOption': 'anothervalue',
        }
    )
    def test_generate_custom_config(
        self,
        generator: ViceGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'c64' / 'rom.d64',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')
