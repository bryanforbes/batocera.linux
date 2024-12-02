from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.tyrian.tyrianGenerator import TyrianGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestTyrianGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert TyrianGenerator().getHotkeysContext() == snapshot

    def test_get_in_game_ratio(self) -> None:
        assert TyrianGenerator().getInGameRatio({}, {'width': 0, 'height': 0}, '') == 16 / 9

    def test_generate(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'tyrian' / 'data')

        command = TyrianGenerator().generate(
            mocker.Mock(),
            '',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot

    def test_generate_not_downloaded(
        self, one_player_controllers: ControllerMapping, mocker: MockerFixture, caplog: pytest.LogCaptureFixture
    ) -> None:
        TyrianGenerator().generate(
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
                'configgen.generators.tyrian.tyrianGenerator',
                logging.ERROR,
                'ERROR: Game assets not installed. You can get them from the Batocera Content Downloader.',
            )
        ]
