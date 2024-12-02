from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.flatpak.flatpakGenerator import FlatpakGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


class TestFlatpakGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[FlatpakGenerator]:
        return FlatpakGenerator

    def test_get_mouse_mode(self, generator: FlatpakGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_generate(
        self, generator: FlatpakGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file(ROMS / 'flatpak' / 'rom.flatpak', contents='\nROMID\n\n  ')
        os_system = mocker.patch('os.system')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'flatpak' / 'rom.flatpak',
                [],
                {},
                [],
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
