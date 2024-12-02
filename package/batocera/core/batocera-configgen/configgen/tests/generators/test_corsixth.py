from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.corsixth.corsixthGenerator import CorsixTHGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestCorsixTHGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[CorsixTHGenerator]:
        return CorsixTHGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'corsixth'

    @pytest.fixture
    def emulator(self) -> str:
        return 'corsixth'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem, request: SubRequest) -> FakeFilesystem:
        if 'no_fs_mods' not in request.keywords:
            fs.create_dir(ROMS / 'corsixth' / 'ANIMS')
            fs.create_dir(ROMS / 'corsixth' / 'DATA')
            fs.create_dir(ROMS / 'corsixth' / 'INTRO')
            fs.create_dir(ROMS / 'corsixth' / 'LEVELS')
            fs.create_dir(ROMS / 'corsixth' / 'QDATA')

        return fs

    @pytest.fixture(autouse=True)
    def subprocess_check_output(self, mocker: MockerFixture) -> Mock:
        return mocker.patch('subprocess.check_output', return_value='fr_FR')

    def test_generate(
        self,
        generator: CorsixTHGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                Path(),
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: CorsixTHGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'corsixth' / 'config.txt', contents='check_for_updates = true\n')

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cth_new_graphics': 'false'},
            {'cth_free_build_mode': 'true'},
            {'cth_play_intro': 'false'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: CorsixTHGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot()

    @pytest.mark.parametrize(
        'lang',
        [
            'foobar',
            'en_US',
            'en_GB',
            'fr_FR',
            'oc_FR',
            'de_DE',
            'es_ES',
            'es_MX',
            'it_IT',
            'nl_NL',
            'ru_RU',
            'sv_SE',
            'cs_CZ',
            'fi_FI',
            'pl_PL',
            'hu_HU',
            'pt_PT',
            'pt_BR',
            'zh_CN',
            'zh_TW',
            'ko_KR',
            'nb_NO',
            'nn_NO',
        ],
    )
    def test_generate_language(
        self,
        generator: CorsixTHGenerator,
        lang: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        subprocess_check_output: Mock,
    ) -> None:
        subprocess_check_output.return_value = lang

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot()

    @pytest.mark.no_fs_mods
    def test_generate_missing_dirs_and_check_output_raises(
        self,
        generator: CorsixTHGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        subprocess_check_output: Mock,
    ) -> None:
        subprocess_check_output.side_effect = subprocess.CalledProcessError(1, [])

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot()

    def test_generate_custom_music(
        self,
        generator: CorsixTHGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(ROMS / 'corsixth' / 'MP3')

        generator.generate(
            mock_system,
            Path(),
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'corsixth' / 'config.txt').read_text() == snapshot()
