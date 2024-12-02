from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.drastic.drasticGenerator import DrasticGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs', 'os_environ_lang')
class TestDrasticGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[DrasticGenerator]:
        return DrasticGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'nds'

    @pytest.fixture
    def emulator(self) -> str:
        return 'drastic'

    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(CONFIGS)
        fs.create_dir('/usr/share/drastic/config')
        fs.create_file('/usr/share/drastic/test.txt')
        fs.create_file('/usr/bin/drastic', contents='drastic bin')

        return fs

    @pytest.fixture
    def grep_return_code(self) -> int:
        return 0

    @pytest.fixture(autouse=True)
    def subprocess_run(
        self, subprocess_run: Mock, mocker: MockerFixture, fs: FakeFilesystem, grep_return_code: int
    ) -> Mock:
        def side_effect(arg: str, *args: Any, **kwargs: Any) -> Any:
            if arg.endswith('> drastic.txt'):
                fs.create_file('/drastic.txt')

            result = mocker.Mock()
            result.returncode = grep_return_code if arg.startswith('grep -q') else 0

            return result

        subprocess_run.side_effect = side_effect

        return subprocess_run

    def test_generate(
        self,
        generator: DrasticGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        subprocess_run: Mock,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'nds' / 'rom.nds',
                one_player_controllers,
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert Path(CONFIGS / 'drastic' / 'test.txt').is_file()
        assert filecmp.cmp('/usr/bin/drastic', Path(CONFIGS / 'drastic' / 'drastic'))
        assert Path(CONFIGS / 'drastic' / 'drastic').stat().st_mode == 0o100775
        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot(name='config')
        assert subprocess_run.call_args_list == snapshot(name='subprocess-run')
        assert not Path('/drastic.txt').exists()

    def test_generate_existing_root(
        self,
        generator: DrasticGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'drastic' / 'drastic', contents='drastic bin')
        fs.create_file(CONFIGS / 'drastic' / 'config' / 'drastic.cfg', contents='foo bar baz')

        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert not Path(CONFIGS / 'drastic' / 'test.txt').exists()
        assert filecmp.cmp('/usr/bin/drastic', Path(CONFIGS / 'drastic' / 'drastic'))
        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot

    def test_generate_old_bin(
        self,
        generator: DrasticGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_dir(CONFIGS / 'drastic' / 'config')
        fs.create_file(CONFIGS / 'drastic' / 'drastic', contents='old drastic bin')

        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert filecmp.cmp('/usr/bin/drastic', Path(CONFIGS / 'drastic' / 'drastic'))

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'drastic_hires': '1'},
            {'drastic_hires': '0'},
            {'drastic_threaded': '1'},
            {'drastic_threaded': '0'},
            {'drastic_fix2d': '1'},
            {'drastic_fix2d': '0'},
            {'drastic_screen_orientation': '1'},
            {'drastic_screen_orientation': '3'},
            {'drastic_screen_orientation': '0'},
            {'drastic_frameskip_value': '1'},
            {'drastic_frameskip_value': '2'},
            {'drastic_frameskip_type': '2'},
            {'drastic_frameskip_type': '3'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: DrasticGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            'ja_JP',
            'en_US',
            'fr_FR',
            'de_DE',
            'it_IT',
            'es_ES',
            'en_GB',
        ],
        indirect=True,
    )
    def test_generate_lang(
        self,
        generator: DrasticGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot

    @pytest.mark.parametrize(
        ('mock_system_config', 'grep_return_code'),
        [
            pytest.param({}, 1, id='no config, grep exits with 1'),
            pytest.param({'drastic_scaling': 'nearest'}, 0, id='nearest, grep exits with 0'),
            pytest.param({'drastic_scaling': 'nearest'}, 1, id='nearest, grep exits with 1'),
            pytest.param({'drastic_scaling': 'bilinear'}, 0, id='bilinear, grep exits with 0'),
        ],
    )
    def test_generate_scaling(
        self,
        generator: DrasticGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        subprocess_run: Mock,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'nds' / 'rom.nds',
            one_player_controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert subprocess_run.call_args_list == snapshot
        # assert not Path('/drastic.txt').exists()
