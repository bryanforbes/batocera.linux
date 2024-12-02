from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.batoceraPaths import ROMS, SAVES
from configgen.generators.uqm.uqmGenerator import UqmGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


class TestUqmGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert UqmGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'uqm')

        assert (
            UqmGenerator().generate(
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

        assert (SAVES / 'uqm' / 'teams').exists()
        assert (SAVES / 'uqm' / 'save').exists()
        assert (ROMS / 'uqm' / 'version').read_text() == ''

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'uqm' / 'version', contents='foo')

        assert (
            UqmGenerator().generate(
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

        assert (ROMS / 'uqm' / 'version').read_text() == 'foo'
