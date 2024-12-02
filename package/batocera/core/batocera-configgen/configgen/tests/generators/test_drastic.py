from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS
from configgen.generators.drastic.drasticGenerator import DrasticGenerator

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs', 'os_environ_lang')
class TestDrasticGenerator:
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

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        assert DrasticGenerator().getHotkeysContext() == snapshot

    def test_generate(
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        assert (
            DrasticGenerator().generate(
                mock_system,
                '/userdata/roms/nds/rom.nds',
                one_player_controllers,
                {},
                {},
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert Path(CONFIGS / 'drastic' / 'test.txt').is_file()
        assert filecmp.cmp('/usr/bin/drastic', Path(CONFIGS / 'drastic' / 'drastic'))
        assert Path(CONFIGS / 'drastic' / 'drastic').stat().st_mode == 0o100775
        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot(name='config')

    def test_generate_existing_root(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'drastic' / 'drastic', contents='drastic bin')
        fs.create_file(CONFIGS / 'drastic' / 'config' / 'drastic.cfg', contents='foo bar baz')

        DrasticGenerator().generate(
            mock_system,
            '/userdata/roms/nds/rom.nds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert not Path(CONFIGS / 'drastic' / 'test.txt').exists()
        assert filecmp.cmp('/usr/bin/drastic', Path(CONFIGS / 'drastic' / 'drastic'))
        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot

    def test_generate_old_bin(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
    ) -> None:
        fs.create_dir(CONFIGS / 'drastic' / 'config')
        fs.create_file(CONFIGS / 'drastic' / 'drastic', contents='old drastic bin')

        DrasticGenerator().generate(
            mock_system,
            '/userdata/roms/nds/rom.nds',
            one_player_controllers,
            {},
            {},
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
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        DrasticGenerator().generate(
            mock_system,
            '/userdata/roms/nds/rom.nds',
            one_player_controllers,
            {},
            {},
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
        self, mock_system: Emulator, one_player_controllers: ControllerMapping, snapshot: SnapshotAssertion
    ) -> None:
        DrasticGenerator().generate(
            mock_system,
            '/userdata/roms/nds/rom.nds',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert Path(CONFIGS / 'drastic' / 'config' / 'drastic.cfg').read_text() == snapshot
