from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SCREENSHOTS
from configgen.generators.sdlpop.sdlpopGenerator import SdlPopGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


class TestSdlPopGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[SdlPopGenerator]:
        return SdlPopGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'sdlpop'

    @pytest.fixture
    def emulator(self) -> str:
        return 'sdlpop'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/share/sdlpop/cfg/SDLPoP.cfg', contents='system config')
        fs.create_file('/usr/share/sdlpop/cfg/SDLPoP.ini', contents='system ini')
        return fs

    def test_generate(
        self,
        generator: SdlPopGenerator,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mock_system,
                ROMS / 'sdlpop' / 'rom.sdlpop',
                two_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'sdlpop' / 'SDLPoP.cfg').read_text() == 'system config'
        assert (CONFIGS / 'sdlpop' / 'SDLPoP.ini').read_text() == 'system ini'
        assert Path('/usr/share/sdlpop/SDLPoP.cfg').resolve() == Path(CONFIGS / 'sdlpop' / 'SDLPoP.cfg')
        assert Path('/usr/share/sdlpop/SDLPoP.ini').resolve() == Path(CONFIGS / 'sdlpop' / 'SDLPoP.ini')
        assert Path('/usr/share/sdlpop/screenshots').resolve() == Path(SCREENSHOTS / 'sdlpop')

    def test_generate_existing(
        self,
        generator: SdlPopGenerator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        two_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(CONFIGS / 'sdlpop' / 'SDLPoP.cfg', contents='user config')
        fs.create_file(CONFIGS / 'sdlpop' / 'SDLPoP.ini', contents='user ini')
        fs.create_file('/usr/share/sdlpop/SDLPoP.cfg')
        fs.create_file('/usr/share/sdlpop/SDLPoP.ini')
        fs.create_dir(SCREENSHOTS / 'sdlpop')

        generator.generate(
            mock_system,
            ROMS / 'sdlpop' / 'rom.sdlpop',
            two_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'sdlpop' / 'SDLPoP.cfg').read_text() == 'user config'
        assert (CONFIGS / 'sdlpop' / 'SDLPoP.ini').read_text() == 'user ini'
        assert not Path('/usr/share/sdlpop/SDLPoP.cfg').is_symlink()
        assert not Path('/usr/share/sdlpop/SDLPoP.ini').is_symlink()
        assert not Path('/usr/share/sdlpop/screenshots').exists()
