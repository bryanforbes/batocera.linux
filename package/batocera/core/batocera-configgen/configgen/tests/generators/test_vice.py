from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.vice.viceGenerator import ViceGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator
    from configgen.types import GunMapping


@pytest.mark.usefixtures('fs')
class TestViceGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'c64'

    @pytest.fixture
    def emulator(self) -> str:
        return 'vice'

    @pytest.fixture
    def core(self) -> str:
        return 'x64'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert ViceGenerator().getHotkeysContext() == snapshot

    def test_get_resolution_mode(self) -> None:
        assert ViceGenerator().getResolutionMode({}) == 'default'

    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            ViceGenerator().generate(
                mock_system,
                '/userdata/roms/c64/rom.d64',
                one_player_controllers,
                {},
                {},
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
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
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

        ViceGenerator().generate(
            mock_system,
            '/userdata/roms/c64/rom.d64',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')

    @pytest.mark.mock_system_config({'noborder': '1'})
    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate_noborder(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        ViceGenerator().generate(
            mock_system,
            '/userdata/roms/c64/rom.d64',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')

    @pytest.mark.mock_system_config({'use_guns': '1'})
    @pytest.mark.parametrize(
        ('guns', 'metadata'),
        [
            pytest.param({}, {}, id='no guns, no metadata'),
            pytest.param({1: {}}, {'gun_type': 'foo'}, id='one gun, gun_type=foo'),
            pytest.param({1: {}}, {'gun_type': 'stack_light_rifle'}, id='one gun, gun_type=stack_light_rifle'),
            pytest.param({}, {'gun_type': 'stack_light_rifle'}, id='no guns, gun_type=stack_light_rifle'),
        ],
    )
    @pytest.mark.parametrize('core', ['x64', 'x64dtv', 'xscpu64', 'xplus4', 'x128', 'xvic', 'xpet'])
    def test_generate_guns(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        guns: GunMapping,
        metadata: dict[str, Any],
        snapshot: SnapshotAssertion,
    ) -> None:
        ViceGenerator().generate(
            mock_system,
            '/userdata/roms/c64/rom.d64',
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
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        ViceGenerator().generate(
            mock_system,
            '/userdata/roms/c64/rom.d64',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'vice' / 'sdl-vicerc').read_text() == snapshot(name='vicerc')
