from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.sonicretro.sonicretroGenerator import SonicRetroGenerator, _get_resolved_path_md5
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestSonicRetroGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SonicRetroGenerator]:
        return SonicRetroGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'sonicretro'

    @pytest.fixture
    def emulator(self) -> str:
        return 'sonic2013'

    @pytest.fixture(autouse=True)
    def reset_md5_cache(self) -> None:
        # Since the MD5 cache is based on path and we use the same rom name across multiple tests,
        # we have to manually delete the cache to ensure new hashes get populated.
        _get_resolved_path_md5.cache_clear()

    @pytest.fixture
    def md5(self, mocker: MockerFixture) -> Mock:
        # This mocks the md5 HASH instance by taking the contents of the file and returning it as
        # a string from the hexdigest function
        def md5_side_effect(contents: bytes, /) -> Mock:
            mock_hash = mocker.Mock()
            mock_hash.hexdigest.return_value = contents.decode('utf-8')
            return mock_hash

        return mocker.patch('hashlib.md5', side_effect=md5_side_effect)

    @pytest.mark.usefixtures('md5')
    @pytest.mark.parametrize(
        ('rom_dir', 'hash', 'result'),
        [
            pytest.param('rom.son', '', False, id='sonic2013'),
            pytest.param('rom.scd', 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', False, id='soniccd, not iOS'),
            pytest.param('rom.scd', '1bd5ad366df1765c98d20b53c092a528', True, id='soniccd, iOS'),
        ],
    )
    def test_get_mouse_mode(  # pyright: ignore
        self, generator: SonicRetroGenerator, rom_dir: str, hash: str, fs: FakeFilesystem, result: bool
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / rom_dir / 'Data.rsdk', contents=hash)

        assert generator.getMouseMode(SystemConfig({}), ROMS / 'sonicretro' / f'{rom_dir}') == result

    @pytest.mark.parametrize('rom_dir', ['rom.son', 'rom.scd'])
    def test_generate(
        self,
        generator: SonicRetroGenerator,
        rom_dir: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / rom_dir / 'Data.rsdk')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'sonicretro' / f'{rom_dir}',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'sonicretro' / rom_dir / 'settings.ini').read_text() == snapshot(name='config')

    def test_generate_existing(
        self,
        generator: SonicRetroGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / 'rom.son' / 'Data.rsdk')
        fs.create_file(
            ROMS / 'sonicretro' / 'rom.son' / 'settings.ini',
            contents="""[Dev]
DevMenu=true
""",
        )

        generator.generate(
            mock_system,
            ROMS / 'sonicretro' / 'rom.son',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'sonicretro' / 'rom.son' / 'settings.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'devmenu': '0'},
            {'devmenu': '1'},
            {'hqmode': '0'},
            {'hqmode': '1'},
            {'skipstart': '0'},
            {'skipstart': '1'},
            {'language': '1'},
            {'vsync': '0'},
            {'vsync': '1'},
            {'scalingmode': '0'},
        ],
        ids=str,
    )
    def test_generate_config_sonic2013(
        self,
        generator: SonicRetroGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / 'rom.son' / 'Data.rsdk')

        generator.generate(
            mock_system,
            ROMS / 'sonicretro' / 'rom.son',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'sonicretro' / 'rom.son' / 'settings.ini').read_text() == snapshot

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'devmenu': '0'},
            {'devmenu': '1'},
            {'hqmode': '0'},
            {'hqmode': '1'},
            {'spindash': '0'},
            {'language': '1'},
            {'vsync': '0'},
            {'vsync': '1'},
            {'scalingmode': '0'},
        ],
        ids=str,
    )
    def test_generate_config_soniccd(
        self,
        generator: SonicRetroGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / 'rom.scd' / 'Data.rsdk')

        generator.generate(
            mock_system,
            ROMS / 'sonicretro' / 'rom.scd',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'sonicretro' / 'rom.scd' / 'settings.ini').read_text() == snapshot

    def test_generate_no_player_one(
        self,
        generator: SonicRetroGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / 'rom.son' / 'Data.rsdk')

        generator.generate(
            mock_system,
            ROMS / 'sonicretro' / 'rom.son',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'sonicretro' / 'rom.son' / 'settings.ini').read_text() == snapshot

    @pytest.mark.usefixtures('md5')
    @pytest.mark.parametrize(
        'hash',
        [
            # Sonic 1
            '5250b0e2effa4d48894106c7d5d1ad32',
            '5771433883e568715e7ac994bb22f5ed',
            # Sonic 2
            'f958285af4a09d2023b4e4f453691c4f',
            '9fe2dae0a8a2c7d8ef0bed639b3c749f',
            # Sonic CD
            'e723aab26026e4e6d4522c4356ef5a98',
            # something else
            'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
        ],
    )
    def test_generate_game_config_bin(
        self,
        generator: SonicRetroGenerator,
        hash: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / 'sonicretro' / 'rom.son' / 'Data.rsdk')
        fs.create_file(ROMS / 'sonicretro' / 'rom.son' / 'Data' / 'Game' / 'GameConfig.bin', contents=hash)

        generator.generate(
            mock_system,
            ROMS / 'sonicretro' / 'rom.son',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (ROMS / 'sonicretro' / 'rom.son' / 'settings.ini').read_text() == snapshot
