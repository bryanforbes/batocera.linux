from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.generators.dosboxstaging.dosboxstagingGenerator import DosBoxStagingGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestDosBoxStagingGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DosBoxStagingGenerator().getHotkeysContext() == snapshot

    def test_generate(self, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        assert (
            DosBoxStagingGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/dos/rom.pc',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_conf(self, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        fs.create_file('/userdata/roms/dos/rom.pc/dosbox.cfg')

        assert (
            DosBoxStagingGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/dos/rom.pc',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
