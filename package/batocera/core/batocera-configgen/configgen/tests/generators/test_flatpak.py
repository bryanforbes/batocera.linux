from __future__ import annotations

from typing import TYPE_CHECKING

from configgen.batoceraPaths import ROMS
from configgen.generators.flatpak.flatpakGenerator import FlatpakGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestFlatpakGenerator:
    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert FlatpakGenerator().getHotkeysContext() == snapshot

    def test_get_mouse_mode(self) -> None:
        assert FlatpakGenerator().getMouseMode({}, '')

    def test_generate(self, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion) -> None:
        fs.create_file(ROMS / 'flatpak' / 'rom.flatpak', contents='\nROMID\n\n  ')
        os_system = mocker.patch('os.system')

        assert (
            FlatpakGenerator().generate(
                mocker.Mock(),
                '/userdata/roms/flatpak/rom.flatpak',
                {},
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        os_system.assert_has_calls(
            [  # pyright: ignore
                mocker.call('chown -R root:audio /var/run/pulse'),
                mocker.call('chmod -R g+rwX /var/run/pulse'),
            ]
        )
