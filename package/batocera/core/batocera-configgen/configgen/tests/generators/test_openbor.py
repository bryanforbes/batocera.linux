from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.openbor.openborGenerator import OpenborGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers
    from configgen.Emulator import Emulator


class TestOpenborGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenborGenerator]:
        return OpenborGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'openbor'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openbor'

    @pytest.fixture
    def core(self) -> str:
        return 'openbor4432'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_dir(ROMS / 'openbor')
        return fs

    def test_generate(
        self,
        generator: OpenborGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'openbor' / 'rom.pak',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openbor' / 'config7530.ini').read_text() == snapshot(name='config')
        assert fs.cwd == '/userdata/roms/openbor'

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'openbor_ratio': '1'},
            {'openbor_filter': '1'},
            {'openbor_vsync': '0'},
            {'openbor_limit': '1'},
            {'openbor_rumble': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: OpenborGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'openbor' / 'rom.pak',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openbor' / 'config7530.ini').read_text() == snapshot

    @pytest.mark.mock_system_config({'core-forced': True})
    @pytest.mark.parametrize('core', ['openbor4432', 'openbor6412', 'openbor7142', 'openbor7530', 'unknown'])
    def test_generate_forced_core(
        self,
        generator: OpenborGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'openbor' / 'rom.pak',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        core = mock_system.config['core']
        core_number = '7530' if core == 'unknown' else core[-4:]
        assert (CONFIGS / 'openbor' / f'config{core_number}.ini').read_text() == snapshot(
            name=f'config{core_number}.ini'
        )

    @pytest.mark.parametrize(
        ('rom_name', 'core_number'),
        [
            ('rom[5438]', '4432'),
            ('rom[6000]', '6412'),
            ('rom[6500]', '7142'),
            ('rom[7530]', '7530'),
        ],
    )
    def test_generate_guessed_core(
        self,
        generator: OpenborGenerator,
        rom_name: str,
        core_number: str,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'openbor' / f'{rom_name}.pak',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'openbor' / f'config{core_number}.ini').read_text() == snapshot(
            name=f'config{core_number}.ini'
        )

    @pytest.mark.mock_system_config({'core-forced': True})
    @pytest.mark.parametrize('core', ['openbor4432', 'openbor7142', 'openbor7530'])
    def test_generate_controllers(
        self,
        generator: OpenborGenerator,
        mock_system: Emulator,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        generator.generate(
            mock_system,
            ROMS / 'openbor' / 'rom.pak',
            make_player_controller_list(ps3_controller, keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'openbor' / f'config{mock_system.config["core"][-4:]}.ini').read_text() == snapshot
