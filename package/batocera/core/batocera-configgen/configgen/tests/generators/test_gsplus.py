from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.gsplus.gsplusGenerator import GSplusGenerator

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestGSplusGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert GSplusGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self, one_player_controllers: ControllerMapping, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            GSplusGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/apple2/rom.po',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize('extension', ['dsk', 'do', 'nib'])
    def test_generate_roms(
        self,
        extension: str,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        GSplusGenerator().generate(
            mocker.Mock(),
            f'/userdata/roms/apple2/rom.{extension}',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'GSplus' / 'config.txt').read_text() == snapshot(name='config')
