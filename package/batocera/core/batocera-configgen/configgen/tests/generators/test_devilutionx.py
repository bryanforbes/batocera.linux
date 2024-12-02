from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, SAVES
from configgen.generators.devilutionx.devilutionxGenerator import DevilutionXGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestDevilutionXGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'devilutionx'

    @pytest.fixture
    def emulator(self) -> str:
        return 'devilutionx'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DevilutionXGenerator().getHotkeysContext() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [
            ({}, 4 / 3),
            ({'devilutionx_stretch': 'false'}, 4 / 3),
            ({'devilutionx_stretch': 'true'}, 16 / 9),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(self, mock_system_config: dict[str, Any], result: bool) -> None:
        assert DevilutionXGenerator().getInGameRatio(mock_system_config, {'width': 0, 'height': 0}, '') == result

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        command = DevilutionXGenerator().generate(
            mock_system,
            '/userdata/roms/devilutionx/diablo.mpq',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (SAVES / 'devilutionx').is_dir()
        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            CONFIGS / 'devilutionx' / 'diablo.ini',
            contents="""[Graphics]
foo = 1

[Something]
bar = 0
""",
        )

        DevilutionXGenerator().generate(
            mock_system,
            '/userdata/roms/devilutionx/diablo.mpq',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot()

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'devilutionx_stretch': 'true'},
            {'devilutionx_stretch': 'false'},
            {'showFPS': 'true'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = DevilutionXGenerator().generate(
            mock_system,
            '/userdata/roms/devilutionx/diablo.mpq',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'devilutionx' / 'diablo.ini').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom',
        [
            'hellfire.mpq',
            'spawn.mpq',
            'foo.mpq',
        ],
    )
    def test_generate_rom(
        self,
        rom: str,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = DevilutionXGenerator().generate(
            mock_system,
            f'/userdata/roms/devilutionx/{rom}',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
