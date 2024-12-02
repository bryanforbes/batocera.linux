from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.openjazz.openjazzGenerator import OpenJazzGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestOpenJazzGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'openjazz'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openjazz'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert OpenJazzGenerator().getHotkeysContext() == snapshot

    def test_get_in_game_ratio(self) -> None:
        assert OpenJazzGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            OpenJazzGenerator().generate(
                mock_system,
                '/userdata/roms/openjazz/rom.game',
                one_player_controllers,
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        # config file with 640x480 resolution
        fs.create_file(
            CONFIGS / 'openjazz' / 'openjazz.cfg',
            contents=b'\x06\x80\x02\xe0\x01\x03R\x00\x00@Q\x00\x00@P\x00\x00@O\x00\x00@ \x00\x00\x00 \x00\x00\x00\xe2\x00\x00@\xe4\x00\x00@\r\x00\x00\x00\x1b\x00\x00\x001\x00\x00\x002\x00\x00\x003\x00\x00\x004\x00\x00\x005\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x03\x00\x00\x00\t\x00\x00\x00\x08\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x04\x00\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x01\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x08\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00Jazz\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xff\xff\xff\xff\xff\xff\x00',
        )

        OpenJazzGenerator().generate(
            mock_system,
            '/userdata/roms/openjazz/rom.game',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')

    @pytest.mark.mock_system_config({'jazz_resolution': '640x480'})
    def test_generate_config(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        OpenJazzGenerator().generate(
            mock_system,
            '/userdata/roms/openjazz/rom.game',
            one_player_controllers,
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openjazz' / 'openjazz.cfg').read_bytes() == snapshot(name='config')
