from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.etlegacy.etlegacyGenerator import ETLegacyGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestETLegacyGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ETLegacyGenerator]:
        return ETLegacyGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'etlegacy'

    @pytest.fixture
    def emulator(self) -> str:
        return 'etlegacy'

    def test_get_mouse_mode(self, generator: ETLegacyGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: ETLegacyGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: ETLegacyGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/share/etlegacy/legacy_2.83-dirty.pk3', contents='pk3')

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
        assert (CONFIGS / 'etlegacy' / 'legacy' / 'etconfig.cfg').read_text() == snapshot(name='config')
        assert filecmp.cmp(
            '/usr/share/etlegacy/legacy_2.83-dirty.pk3', ROMS / 'etlegacy' / 'legacy' / 'legacy_2.83-dirty.pk3'
        )

    def test_generate_existing(
        self,
        generator: ETLegacyGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/share/etlegacy/legacy_2.83-dirty.pk3', contents='pk3')
        fs.create_file(ROMS / 'etlegacy' / 'legacy' / 'legacy_2.83-dirty.pk3', contents='new pk3')
        fs.create_file(
            CONFIGS / 'etlegacy' / 'legacy' / 'etconfig.cfg',
            contents="""seta r_mode "2"
seta r_fullscreen "0"
seta r_allowResize "1"
seta r_customheight ""640""
seta r_customwidth ""480""
seta cl_lang "af"
seta ui_cl_lang "af"
seta foo "bar"
""",
        )

        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'etlegacy' / 'legacy' / 'etconfig.cfg').read_text() == snapshot
        assert (ROMS / 'etlegacy' / 'legacy' / 'legacy_2.83-dirty.pk3').read_text() == 'new pk3'

    def test_generate_old_pk3(
        self,
        generator: ETLegacyGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
    ) -> None:
        fs.create_file(ROMS / 'etlegacy' / 'legacy' / 'legacy_2.83-dirty.pk3', contents='old pk3')
        fs.create_file('/usr/share/etlegacy/legacy_2.83-dirty.pk3', contents='pk3')

        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'etlegacy' / 'legacy' / 'legacy_2.83-dirty.pk3').read_text() == 'pk3'

    @pytest.mark.mock_system_config({'etlegacy_language': 'af'})
    def test_generate_language(
        self,
        generator: ETLegacyGenerator,
        mock_system: Emulator,
        fs: FakeFilesystem,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/usr/share/etlegacy/legacy_2.83-dirty.pk3', contents='pk3')

        generator.generate(
            mock_system,
            Path(),
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'etlegacy' / 'legacy' / 'etconfig.cfg').read_text() == snapshot
