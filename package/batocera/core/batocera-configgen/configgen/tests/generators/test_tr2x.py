from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.tr2x.tr2xGenerator import TR2XGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerList
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


class TestTR2XGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TR2XGenerator]:
        return TR2XGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'traider1'

    @pytest.fixture
    def emulator(self) -> str:
        return 'tr1x'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(ROMS / 'traider2' / 'Tomb Raider 2.croft')
        fs.create_file('/usr/bin/tr2x/TR2X', contents='tr2x bin')
        fs.create_file('/usr/bin/tr2x/foo/bar', contents='bar')
        fs.create_file('/usr/bin/tr2x/foo/ham/spam', contents='spam')
        return fs

    @pytest.fixture
    def copytree(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('shutil.copytree')

    @pytest.mark.parametrize(
        ('resolution', 'result'),
        [
            ({'width': 640, 'height': 480}, 4 / 3),
            ({'width': 1920, 'height': 1080}, 16 / 9),
            ({'width': 1920, 'height': 1144}, 16 / 9),
            ({'width': 1920, 'height': 1145}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: TR2XGenerator, resolution: Resolution, result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig({}), resolution, Path()) == result

    def test_generate(
        self,
        generator: TR2XGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider2' / 'Tomb Raider 2.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider2' / 'cfg' / 'TR2X.json5').read_text() == snapshot(name='config')

        assert (ROMS / 'traider2' / 'TR2X').read_text() == 'tr2x bin'
        assert (ROMS / 'traider2' / 'foo' / 'bar').read_text() == 'bar'
        assert (ROMS / 'traider2' / 'foo' / 'ham' / 'spam').read_text() == 'spam'

    def test_generate_second_run(
        self,
        generator: TR2XGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'traider2' / 'music')
        fs.create_file(ROMS / 'traider2' / 'TRX2', contents='old tr2x bin')
        fs.create_file(ROMS / 'traider2' / 'foo' / 'bar', contents='old bar')
        fs.create_file(ROMS / 'traider2' / 'foo' / 'ham' / 'spam', contents='old spam')
        fs.create_file(ROMS / 'traider2' / 'cfg' / 'TR2X.json5', contents='{ "foo": "bar" }')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider2' / 'Tomb Raider 2.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider2' / 'cfg' / 'TR2X.json5').read_text() == snapshot(name='config')

        assert (ROMS / 'traider2' / 'TR2X').read_text() == 'tr2x bin'
        assert (ROMS / 'traider2' / 'foo' / 'bar').read_text() == 'bar'
        assert (ROMS / 'traider2' / 'foo' / 'ham' / 'spam').read_text() == 'spam'

    @pytest.mark.parametrize('exception', [PermissionError(), Exception()])
    def test_generate_ignores_copy_errors(
        self,
        generator: TR2XGenerator,
        mock_system: Emulator,
        copytree: Mock,
        exception: Exception,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        copytree.side_effect = exception

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider2' / 'Tomb Raider 2.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider2' / 'cfg' / 'TR2X.json5').read_text() == snapshot(name='config')

    def test_generate_ignores_json_errors(
        self,
        fs: FakeFilesystem,
        generator: TR2XGenerator,
        mock_system: Emulator,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'traider2' / 'cfg' / 'TR2X.json5', contents='{{')
        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider2' / 'Tomb Raider 2.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider2' / 'cfg' / 'TR2X.json5').read_text() == snapshot(name='config')
