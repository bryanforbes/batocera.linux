from __future__ import annotations

import io
from pathlib import Path
from typing import TYPE_CHECKING
from zipfile import BadZipFile, ZipFile

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.tr1x.tr1xGenerator import TR1XGenerator
from configgen.utils.download import DownloadException
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerList
    from configgen.Emulator import Emulator
    from configgen.types import Resolution


class TestTR1XGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[TR1XGenerator]:
        return TR1XGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'traider1'

    @pytest.fixture
    def emulator(self) -> str:
        return 'tr1x'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file(ROMS / 'traider1' / 'Tomb Raider.croft')
        fs.create_file('/usr/bin/tr1x/TR1X', contents='tr1x bin')
        fs.create_file('/usr/bin/tr1x/foo/bar', contents='bar')
        fs.create_file('/usr/bin/tr1x/foo/ham/spam', contents='spam')
        return fs

    @pytest.fixture(autouse=True)
    def download(self, mocker: MockerFixture) -> Mock:
        def side_effect(url: str, _: Path) -> Mock:
            zip_content = io.BytesIO()

            with ZipFile(zip_content, 'w') as zip:
                if url.endswith('/music.zip'):
                    zip.writestr('music/foo.txt', '')
                elif url.endswith('/trub-music.zip'):
                    zip.writestr('bar.txt', '')
                    zip.writestr('DATA/', '')
                    zip.writestr('DATA/CAT.PHD', '')

            zip_content.seek(0)

            mock = mocker.MagicMock()
            mock.__enter__.return_value = zip_content

            return mock

        download = mocker.patch('configgen.generators.tr1x.tr1xGenerator.download')
        download.side_effect = side_effect

        return download

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
        self, generator: TR1XGenerator, resolution: Resolution, result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig({}), resolution, Path()) == result

    def test_generate(
        self,
        generator: TR1XGenerator,
        mock_system: Emulator,
        download: Mock,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider1' / 'music' / 'foo.txt').exists()
        assert (ROMS / 'traider1' / 'TR1X').read_text() == 'tr1x bin'
        assert (ROMS / 'traider1' / 'foo' / 'bar').read_text() == 'bar'
        assert (ROMS / 'traider1' / 'foo' / 'ham' / 'spam').read_text() == 'spam'
        download.assert_called_once_with('https://lostartefacts.dev/aux/tr1x/music.zip', ROMS / 'traider1')

    def test_generate_second_run(
        self,
        generator: TR1XGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        download: Mock,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'traider1' / 'music')
        fs.create_file(ROMS / 'traider1' / 'TRX1', contents='old tr1x bin')
        fs.create_file(ROMS / 'traider1' / 'foo' / 'bar', contents='old bar')
        fs.create_file(ROMS / 'traider1' / 'foo' / 'ham' / 'spam', contents='old spam')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'traider1' / 'TR1X').read_text() == 'tr1x bin'
        assert (ROMS / 'traider1' / 'foo' / 'bar').read_text() == 'bar'
        assert (ROMS / 'traider1' / 'foo' / 'ham' / 'spam').read_text() == 'spam'
        download.assert_not_called()

    @pytest.mark.parametrize('exception', [PermissionError(), Exception()])
    def test_generate_ignores_copy_errors(
        self,
        generator: TR1XGenerator,
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
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.parametrize('exception', [DownloadException(), BadZipFile(), Exception()])
    def test_generate_ignores_music_download_errors(
        self,
        generator: TR1XGenerator,
        mock_system: Emulator,
        download: Mock,
        exception: Exception,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        download.side_effect = exception

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    @pytest.mark.mock_system_config({'tr1x-expansion': '1'})
    def test_generate_expansion(
        self,
        mocker: MockerFixture,
        generator: TR1XGenerator,
        mock_system: Emulator,
        download: Mock,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (ROMS / 'traider1' / 'music' / 'foo.txt').exists()
        assert (ROMS / 'traider1' / 'data' / 'CAT.PHD').exists()
        assert (ROMS / 'traider1' / 'data' / 'bar.txt').exists()

        assert download.call_args_list == [
            mocker.call('https://lostartefacts.dev/aux/tr1x/music.zip', ROMS / 'traider1'),
            mocker.call('https://lostartefacts.dev/aux/tr1x/trub-music.zip', ROMS / 'traider1'),
        ]

    @pytest.mark.mock_system_config({'tr1x-expansion': '1'})
    def test_generate_expansion_downloaded(
        self,
        generator: TR1XGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        download: Mock,
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'traider1' / 'music')
        fs.create_file(ROMS / 'traider1' / 'data' / 'CAT.PHD')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        download.assert_not_called()

    @pytest.mark.parametrize('exception', [DownloadException(), BadZipFile(), Exception()])
    @pytest.mark.mock_system_config({'tr1x-expansion': '1'})
    def test_generate_ignores_expansion_download_errors(
        self,
        generator: TR1XGenerator,
        mock_system: Emulator,
        download: Mock,
        exception: type[Exception],
        one_player_controllers: ControllerList,
        snapshot: SnapshotAssertion,
    ) -> None:
        download.side_effect = exception

        assert (
            generator.generate(
                mock_system,
                ROMS / 'traider1' / 'Tomb Raider.croft',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
