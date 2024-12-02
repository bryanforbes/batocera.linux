from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.dosboxx.dosboxxGenerator import DosBoxxGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestDosBoxxGenerator:
    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS / 'dosbox')

        return fs

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DosBoxxGenerator().getHotkeysContext() == snapshot

    def test_generate(self, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        command = DosBoxxGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/dos/rom.pc',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')

    def test_generate_existing(self, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosboxx.conf',
            contents="""[something]
foo = true

[sdl]
bar = false
""",
        )

        command = DosBoxxGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/dos/rom.pc',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')

    def test_generate_game_config(self, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        fs.create_file(
            CONFIGS / 'dosbox' / 'dosboxx.conf',
            contents="""[something]
foo = true
""",
        )
        fs.create_file(
            '/userdata/roms/dos/rom.pc/dosbox.cfg',
            contents="""[something]
foo = false
""",
        )

        command = DosBoxxGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/dos/rom.pc',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
        assert (CONFIGS / 'dosbox' / 'dosboxx-custom.conf').read_text() == snapshot(name='config')
