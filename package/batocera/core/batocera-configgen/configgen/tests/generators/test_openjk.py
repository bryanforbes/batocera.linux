from __future__ import annotations

import filecmp
import stat
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.openjk.openjkGenerator import OpenJKGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures('fs')
class TestOpenJKGeneratorGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[OpenJKGenerator]:
        return OpenJKGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'jknight'

    @pytest.fixture
    def emulator(self) -> str:
        return 'openjk'

    @pytest.fixture(autouse=True)
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/JediAcademy/openjk_sp.x86_64', contents='openjk_sp.x86_64')
        fs.create_file('/usr/bin/JediAcademy/foo.jk.txt', contents='foo.jk.txt')
        fs.create_file('/usr/bin/JediAcademy/ham/spam.jk.txt', contents='spam.jk.txt')
        fs.create_file('/usr/bin/JediOutcast/openjo_sp.x86_64', contents='openjo_sp.x86_64')
        fs.create_file('/usr/bin/JediOutcast/foo.jo.txt', contents='foo.jo.txt')
        fs.create_file('/usr/bin/JediOutcast/ham/spam.jo.txt', contents='spam.jo.txt')

        return fs

    def test_get_mouse_mode(self, generator: OpenJKGenerator) -> None:  # pyright: ignore
        assert generator.getMouseMode(SystemConfig({}), Path())

    def test_get_in_game_ratio(self, generator: OpenJKGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 1920, 'height': 1080}, Path()) == 16 / 9

    @pytest.mark.parametrize(
        'rom',
        [
            'Star Wars Jedi Knight - Jedi Academy',
            'Star Wars Jedi Knight II - Jedi Outcast',
        ],
        ids=['academy', 'outcast'],
    )
    def test_generate(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        rom_dir = ROMS / 'jknight' / rom
        fs.create_dir(rom_dir)

        assert (
            generator.generate(
                mock_system,
                rom_dir / f'{rom}.jedi',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        is_academy = 'Academy' in rom
        game_char = 'k' if is_academy else 'o'
        prefix = f'openj{game_char}'
        bin = rom_dir / f'{prefix}_sp.x86_64'
        config_dir = CONFIGS / prefix
        assert filecmp.cmp(
            bin,
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/{bin.name}',
        )
        assert filecmp.cmp(
            rom_dir / f'foo.j{game_char}.txt',
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/foo.j{game_char}.txt',
        )
        assert filecmp.cmp(
            rom_dir / 'ham' / f'spam.j{game_char}.txt',
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/ham/spam.j{game_char}.txt',
        )
        assert stat.filemode(bin.stat().st_mode) == snapshot(name='filemode')
        assert (config_dir / 'base' / f'{prefix}_sp.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom',
        [
            'Star Wars Jedi Knight - Jedi Academy',
            'Star Wars Jedi Knight II - Jedi Outcast',
        ],
        ids=['academy', 'outcast'],
    )
    def test_generate_existing_binary(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        rom_dir = ROMS / 'jknight' / rom
        is_academy = 'Academy' in rom
        game_char = 'k' if is_academy else 'o'
        prefix = f'openj{game_char}'
        bin = rom_dir / f'{prefix}_sp.x86_64'

        fs.create_dir(rom_dir)
        fs.create_file(bin, contents='new bin')

        generator.generate(
            mock_system,
            rom_dir / f'{rom}.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert bin.read_text() == 'new bin'
        assert not (rom_dir / f'foo.j{game_char}.txt').exists()
        assert not (rom_dir / 'ham' / f'spam.j{game_char}.txt').exists()
        assert stat.filemode(bin.stat().st_mode) == snapshot(name='filemode')

    @pytest.mark.parametrize(
        'rom',
        [
            'Star Wars Jedi Knight - Jedi Academy',
            'Star Wars Jedi Knight II - Jedi Outcast',
        ],
        ids=['academy', 'outcast'],
    )
    def test_generate_existing_old_binary(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        rom_dir = ROMS / 'jknight' / rom
        is_academy = 'Academy' in rom
        game_char = 'k' if is_academy else 'o'
        prefix = f'openj{game_char}'
        bin = rom_dir / f'{prefix}_sp.x86_64'

        fs.create_dir(rom_dir)
        fs.create_file(bin, contents='old bin')
        fs.utime(str(bin), (0, 0))

        generator.generate(
            mock_system,
            rom_dir / f'{rom}.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert filecmp.cmp(
            bin,
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/{bin.name}',
        )
        assert filecmp.cmp(
            rom_dir / f'foo.j{game_char}.txt',
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/foo.j{game_char}.txt',
        )
        assert filecmp.cmp(
            rom_dir / 'ham' / f'spam.j{game_char}.txt',
            f'/usr/bin/{"JediAcademy" if is_academy else "JediOutcast"}/ham/spam.j{game_char}.txt',
        )
        assert stat.filemode(bin.stat().st_mode) == snapshot(name='filemode')

    def test_generate_raises(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
    ) -> None:
        rom_dir = ROMS / 'jknight' / 'foo'
        fs.create_dir(rom_dir)

        with pytest.raises(BatoceraException, match=r'^Could not determine game$'):
            generator.generate(
                mock_system,
                rom_dir / 'foo.jedi',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'openjk_colour': 'None'},
            {'openjk_colour': '16'},
            {'openjk_colour': '32'},
            {'openjk_detail': 'Low'},
            {'openjk_detail': 'Medium'},
            {'openjk_detail': 'High'},
            {'openjk_texture': '3'},
            {'openjk_texture': '2'},
            {'openjk_texture': '1'},
            {'openjk_texture': '0'},
            {'openjk_texture_quality': '0'},
            {'openjk_texture_quality': '16'},
            {'openjk_texture_quality': '32'},
            {'openjk_texture_filter': 'GL_LINEAR_MIPMAP_NEAREST'},
            {'openjk_texture_filter': 'GL_LINEAR_MIPMAP_LINEAR'},
            {'openjk_shaders': '0'},
            {'openjk_shaders': '1'},
            {'openjk_vsync': '0'},
            {'openjk_vsync': '1'},
            {'openjk_brightness': '5.000000'},
            {'openjk_shadows': '0'},
            {'openjk_shadows': '1'},
            {'openjk_shadows': '2'},
            {'openjk_lights': '0'},
            {'openjk_lights': '1'},
            {'openjk_glow': '0'},
            {'openjk_glow': '1'},
            {'openjk_flares': '0'},
            {'openjk_flares': '1'},
            {'openjk_wall': '0'},
            {'openjk_wall': '1'},
            {'openjk_anistropic': '4.000000'},
            {'openjk_crosshair': '0'},
            {'openjk_crosshair': '1'},
            {'openjk_target': '0'},
            {'openjk_target': '1'},
            {'openjk_death': '0'},
            {'openjk_death': '3'},
            {'openjk_guns': '0'},
            {'openjk_guns': '1'},
            {'openjk_dismember': '0'},
            {'openjk_dismember': '1'},
            {'openjk_sway': '0'},
            {'openjk_sway': '1'},
            {'openjk_language': 'french'},
            {'openjk_language': 'english'},
            {'openjk_subtitles': '0'},
            {'openjk_subtitles': '1'},
            {'openjk_subtitles': '2'},
        ],
        ids=str,
    )
    @pytest.mark.parametrize(
        'rom',
        [
            'Star Wars Jedi Knight - Jedi Academy',
            'Star Wars Jedi Knight II - Jedi Outcast',
        ],
        ids=['academy', 'outcast'],
    )
    def test_generate_config(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        rom_dir = ROMS / 'jknight' / rom
        fs.create_dir(rom_dir)

        generator.generate(
            mock_system,
            rom_dir / f'{rom}.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        is_academy = 'Academy' in rom
        prefix = f'openj{"k" if is_academy else "o"}'
        assert (CONFIGS / prefix / 'base' / f'{prefix}_sp.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'rom',
        [
            'Star Wars Jedi Knight - Jedi Academy',
            'Star Wars Jedi Knight II - Jedi Outcast',
        ],
        ids=['academy', 'outcast'],
    )
    def test_generate_existing_config(
        self,
        fs: FakeFilesystem,
        generator: OpenJKGenerator,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
        rom: str,
    ) -> None:
        rom_dir = ROMS / 'jknight' / rom
        fs.create_dir(rom_dir)

        is_academy = 'Academy' in rom
        prefix = f'openj{"k" if is_academy else "o"}'
        fs.create_file(
            CONFIGS / prefix / 'base' / f'{prefix}_sp.cfg',
            contents="""seta r_mode "3"
seta r_fullscreen "1"
seta r_centerWindow "1"
seta r_customheight "1080"
seta r_customwidth "1920"
seta r_picmip "0"
seta r_textureMode "GL_LINEAR_MIPMAP_LINEAR"
seta r_gamma "1.000000"
seta d_slowmodeath "0"
seta cg_shadows "1"
seta r_dynamiclight "1"

seta r_colorbits "16"
seta r_depthbits "16"
seta r_lodbias "2"
seta r_subdivisions "20"
seta r_texturebits "16"
seta r_detailtextures "0"
seta r_swapInterval "1"
seta r_DynamicGlow "1"
""",
        )

        generator.generate(
            mock_system,
            rom_dir / f'{rom}.jedi',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / prefix / 'base' / f'{prefix}_sp.cfg').read_text() == snapshot(name='config')
