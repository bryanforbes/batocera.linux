from __future__ import annotations

import stat
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS, SAVES, USER_SCRIPTS
from tests.generators.libretro.base import LibretroBaseCoreTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('tgbdual')
@pytest.mark.fallback_system_name('gb2players')
class TestLibretroGeneratorTGBDual(LibretroBaseCoreTest):
    @pytest.mark.parametrize('mock_system_config', [{}, {'sync_saves': '0'}], ids=str)
    @pytest.mark.parametrize('has_prefixes', [True, False], ids=['prefixes', 'no prefixes'])
    @pytest.mark.parametrize('extension', ['gb2', 'gbc2'])
    @pytest.mark.parametrize_systems
    def test_generate_two_players(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        extension: str,
        has_prefixes: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(
            ROMS / mock_system.name / f'rom.{extension}',
            contents="""gb:foo:bar.zip
gbc:foo:baz.zip
"""
            if has_prefixes
            else """foo:bar.zip
foo:baz.zip
""",
        )

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / f'rom.{extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert not (SAVES / 'gb').exists()
        assert not (SAVES / 'gbc').exists()
        assert not (SAVES / 'gb2players').exists()
        assert not (SAVES / 'gbc2players').exists()
        assert not (USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh').exists()

    @pytest.mark.mock_system_config({'sync_saves': '1'})
    @pytest.mark.parametrize('savefile_exists', [True, False], ids=['save exists', 'no save'])
    @pytest.mark.parametrize('script_exists', [True, False], ids=['has existing script', 'no existing script'])
    @pytest.mark.parametrize_systems
    def test_generate_one_rom_sync_saves(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        savefile_exists: bool,
        script_exists: bool,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        if script_exists:
            fs.create_file(USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh', contents='old script file')

        if savefile_exists:
            fs.create_file(SAVES / ('gb' if mock_system.name == 'gb2players' else 'gbc') / 'rom.srm')

        fs.create_file(ROMS / mock_system.name / 'rom.gb')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / 'rom.gb',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'gb').exists()
        assert (SAVES / 'gbc').exists()
        assert (SAVES / 'gb2players').exists()
        assert (SAVES / 'gbc2players').exists()
        assert (USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh').read_text() == snapshot(name='sync script')
        assert stat.filemode((USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh').stat().st_mode) == snapshot(
            name='script filemode'
        )

        if savefile_exists:
            assert (SAVES / mock_system.name / 'rom.srm').exists()
        else:
            assert not (SAVES / mock_system.name / 'rom.srm').exists()

    @pytest.mark.parametrize('savefile_exists', [True, False], ids=['save exists', 'no save'])
    @pytest.mark.parametrize('script_exists', [True, False], ids=['has existing script', 'no existing script'])
    @pytest.mark.parametrize('has_prefixes', [True, False], ids=['has prefixes', 'no prefixes'])
    @pytest.mark.parametrize('extension', ['gb2', 'gbc2'])
    @pytest.mark.parametrize_systems
    def test_generate_two_roms_sync_saves(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        extension: str,
        savefile_exists: bool,
        has_prefixes: bool,
        script_exists: bool,
        snapshot: SnapshotAssertion,
    ) -> None:
        mock_system.config['sync_saves'] = '1'

        if script_exists:
            fs.create_file(USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh', contents='old script file')

        fs.create_file(
            ROMS / mock_system.name / f'rom.{extension}',
            contents="""gb:foo:bar.zip
gbc:foo:baz.zip
"""
            if has_prefixes
            else """foo:bar.zip
foo:baz.zip
""",
        )

        files = [
            SAVES / ('gb' if has_prefixes else ('gb' if mock_system.name == 'gb2players' else 'gbc')) / 'foo:bar.srm',
            SAVES / ('gbc' if has_prefixes else ('gb' if mock_system.name == 'gb2players' else 'gbc')) / 'foo:baz.srm',
        ]

        if savefile_exists:
            for file in files:
                fs.create_file(file)

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / f'rom.{extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (SAVES / 'gb').exists()
        assert (SAVES / 'gbc').exists()
        assert (SAVES / 'gb2players').exists()
        assert (SAVES / 'gbc2players').exists()
        assert (USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh').read_text() == snapshot(name='sync script')
        assert stat.filemode((USER_SCRIPTS / 'gb2savesync' / 'exitsync.sh').stat().st_mode) == snapshot(
            name='script filemode'
        )

        if savefile_exists:
            for file in files:
                assert (SAVES / mock_system.name / file.with_suffix('.srm').name).exists()
        else:
            for file in files:
                assert not (SAVES / mock_system.name / file.with_suffix('.srm').name).exists()
