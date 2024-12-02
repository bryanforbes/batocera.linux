from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.sh.shGenerator import ShGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestShGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ShGenerator]:
        return ShGenerator

    def test_get_mouse_mode(self, generator: ShGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_generate(
        self,
        generator: ShGenerator,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ports' / 'rom.sh',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert Path('/tmp/gamecontrollerdb.txt').read_text() == snapshot(name='controllerdb')

    def test_generate_run_sh(
        self,
        generator: ShGenerator,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/ports/rom.sh/run.sh')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ports' / 'rom.sh',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
