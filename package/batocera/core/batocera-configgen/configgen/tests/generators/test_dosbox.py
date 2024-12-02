from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.dosbox.dosboxGenerator import DosBoxGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestDosBoxGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DosBoxGenerator().getHotkeysContext() == snapshot

    def test_generate(self, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        command = DosBoxGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/dos/rom.pc',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot

    def test_generate_conf(self, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.cfg')

        command = DosBoxGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/dos/rom.pc',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (command.array, command.env) == snapshot
