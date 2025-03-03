from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS, SAVES
from configgen.generators.ecwolf.ecwolfGenerator import ECWolfGenerator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers


@pytest.mark.usefixtures('fs')
class TestECWolfGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[ECWolfGenerator]:
        return ECWolfGenerator

    def test_generate(
        self,
        generator: ECWolfGenerator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ecwolf' / 'Wolfenstein 3D.ecwolf',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (SAVES / 'ecwolf').is_dir()
        assert (CONFIGS / 'ecwolf' / 'ecwolf.cfg').read_text() == snapshot(name='config')
        assert fs.cwd == '/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf'

    def test_generate_existing(
        self,
        generator: ECWolfGenerator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf')
        fs.create_file(
            CONFIGS / 'ecwolf' / 'ecwolf.cfg',
            contents="""Vid_FullScreen = 0;
Vid_Aspect = 1;
Vid_Vsync = 0;
QuitOnEscape = 0;
JoystickEnabled = 0;
FullScreenWidth = 640;
FullScreenHeight = 480;
Foo = 0;
Bar = 1;
""",
        )

        generator.generate(
            mocker.Mock(),
            ROMS / 'ecwolf' / 'Wolfenstein 3D.ecwolf',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'ecwolf' / 'ecwolf.cfg').read_text() == snapshot(name='config')

    def test_generate_chdir_raises(
        self,
        generator: ECWolfGenerator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf')
        mocker.patch('os.chdir', side_effect=Exception)

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ecwolf' / 'Wolfenstein 3D.ecwolf',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert (CONFIGS / 'ecwolf' / 'ecwolf.cfg').read_text() == snapshot(name='config')

    @pytest.mark.parametrize(
        'contents',
        [
            '--data wl6 --file HD/ECWolf_hdpack.pk3',
            './wolf3d14 --data sd2 --file ../HD/ECWolf_hdpack.pk3',
        ],
    )
    def test_generate_ecwolf_rom(
        self,
        generator: ECWolfGenerator,
        contents: str,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_dir('/userdata/roms/ecwolf/wolf3d14')
        fs.create_file('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf', contents=contents)

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ecwolf' / 'Wolfenstein 3D.ecwolf',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            ),
            fs.cwd,
        ) == snapshot

    def test_generate_ecwolf_rom_chdir_raises(
        self,
        generator: ECWolfGenerator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/ecwolf/wolf3d14')
        fs.create_file('/userdata/roms/ecwolf/Wolfenstein 3D.ecwolf', contents='./wolf3d14')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ecwolf' / 'Wolfenstein 3D.ecwolf',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            ),
            fs.cwd,
        ) == snapshot

    def test_generate_ecwolf_pk3(
        self,
        generator: ECWolfGenerator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/ecwolf/Wolfenstein 3D.pk3')

        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'ecwolf' / 'Wolfenstein 3D.pk3',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
