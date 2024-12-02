from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.hurrican.hurricanGenerator import HurricanGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestHurricanGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert HurricanGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'hurrican' / 'data' / 'levels')

        assert (
            HurricanGenerator().generate(
                mocker.Mock(),
                '',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_not_downloaded(
        self, one_player_controllers: ControllerMapping, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        HurricanGenerator().generate(
            mocker.Mock(),
            '',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert caplog.record_tuples == [
            (
                'configgen.generators.hurrican.hurricanGenerator',
                logging.ERROR,
                'ERROR: Game assets not installed. You can get them from the Batocera Content Downloader.',
            )
        ]
