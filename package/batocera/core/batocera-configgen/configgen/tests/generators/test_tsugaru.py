from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.tsugaru.tsugaruGenerator import TsugaruGenerator

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator


class TestTsugaruGenerator:
    @pytest.fixture
    def system_name(self) -> str:
        return 'fmtowns'

    @pytest.fixture
    def emulator(self) -> str:
        return 'tsugaru'

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert TsugaruGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = TsugaruGenerator().generate(
            mock_system,
            '/userdata/roms/fmtowns/rom.bin',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot

    @pytest.mark.parametrize('extension', ['d88', 'iso', 'cue'])
    def test_generate_extension(
        self,
        extension: str,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = TsugaruGenerator().generate(
            mock_system,
            f'/userdata/roms/fmtowns/rom.{extension}',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cdrom_speed': '2'},
            {'386dx': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        command = TsugaruGenerator().generate(
            mock_system,
            '/userdata/roms/fmtowns/rom.bin',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
