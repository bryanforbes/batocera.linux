from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import BIOS, CONFIGS, ROMS
from configgen.controller import Controller
from configgen.exceptions import BatoceraException
from configgen.generators.hatari.hatariGenerator import HatariGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestHatariGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[HatariGenerator]:
        return HatariGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'atarist'

    @pytest.fixture
    def emulator(self) -> str:
        return 'hatari'

    def test_generate(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='config')
        assert not (CONFIGS / 'hatari' / 'blank.st').exists()

    def test_generate_existing(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'etos256us.img')
        fs.create_file(
            CONFIGS / 'hatari' / 'hatari.cfg',
            contents="""[Joystick1]
nJoyId = 1

[Log]
bConfirmQuit = TRUE

[Screen]
bShowStatusbar = TRUE

[Foo]
bBar = FALSE
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'ram': '1'},
            {'showFPS': '0'},
            {'showFPS': '1'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='config')

    def test_generate_controllers(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                make_player_controller_list(
                    generic_xbox_pad,
                    Controller(
                        name='Mock',
                        type='joystick',
                        guid='-1',
                        player_number=-1,
                        index=-1,
                        real_name='',
                        device_path='',
                        button_count=0,
                        axis_count=0,
                        hat_count=0,
                        inputs_=[],
                    ),
                    generic_xbox_pad,
                    generic_xbox_pad,
                    generic_xbox_pad,
                    generic_xbox_pad,
                ),
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'hatari.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {},
            {'hatari_drive': 'IDE'},
            {'hatari_drive': 'ACSI'},
        ],
        ids=str,
    )
    def test_generate_hd_rom(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.hd',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert not (CONFIGS / 'hatari' / 'blank.st').exists()

    def test_generate_gemdos_rom(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir(CONFIGS / 'hatari')
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.gemdos',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'blank.st').exists()

    def test_generate_gemdos_rom_existing_blank(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'hatari' / 'blank.st', contents='blank')
        fs.create_file(BIOS / 'etos256us.img')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.gemdos',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'hatari' / 'blank.st').read_text() == 'blank'

    @pytest.mark.parametrize(
        ('model', 'bios_prefix'),
        [
            (None, 'etos256'),
            ('520st_auto', 'etos256'),
            ('520st_100', 'tos100'),
            ('520st_102', 'tos102'),
            ('520st_104', 'tos104'),
            ('520st_etos256', 'etos256'),
            ('1040ste_auto', 'etos256'),
            ('1040ste_106', 'tos106'),
            ('1040ste_162', 'tos162'),
            ('1040ste_etos256', 'etos256'),
            ('megaste_auto', 'etos256'),
            ('megaste_205', 'tos205'),
            ('megaste_206', 'tos206'),
            ('megaste_etos256', 'etos256'),
            ('tt_auto', 'etos512'),
            ('tt_306', 'tos306'),
            ('tt_etos512', 'etos512'),
            ('falcon_auto', 'etos512'),
            ('falcon_400', 'tos400'),
            ('falcon_402', 'tos402'),
            ('falcon_404', 'tos404'),
            ('falcon_etos512', 'etos512'),
        ],
        ids=str,
    )
    @pytest.mark.parametrize('language', ['auto', 'us', 'uk', 'de', 'es', 'fr', 'it', 'nl', 'ru', 'se'])
    def test_generate_bios(
        self,
        generator: HatariGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        language: str,
        model: str | None,
        bios_prefix: str,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(BIOS / f'{bios_prefix}{"" if language == "auto" else language}.img')

        mock_system.config['language'] = language

        if model is not None:
            mock_system.config['model'] = model

        assert (
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

    def test_generate_missing_bios(
        self,
        generator: HatariGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
    ) -> None:
        with pytest.raises(BatoceraException, match=r'^No bios found for machine'):
            generator.generate(
                mock_system,
                ROMS / 'atarist' / 'rom.st',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
