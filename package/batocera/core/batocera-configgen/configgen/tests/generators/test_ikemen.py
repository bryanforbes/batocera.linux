from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.generators.ikemen.ikemenGenerator import IkemenGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping


@pytest.mark.usefixtures('fs')
class TestIkemenGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert IkemenGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            IkemenGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/ikemen/rom.ikemen',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        one_player_controllers: ControllerMapping,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json',
            contents="""{
  "KeyConfig": false,
  "JoystickConfig": true,
  "Fullscreen": false,
  "foo": "bar"
}""",
        )
        IkemenGenerator().generate(
            mocker.Mock(),
            '/userdata/roms/ikemen/rom.ikemen',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (ROMS / 'ikemen' / 'rom.ikemen' / 'save' / 'config.json').read_text() == snapshot
