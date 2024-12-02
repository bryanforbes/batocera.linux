from __future__ import annotations

import filecmp
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.exceptions import BatoceraException
from configgen.generators.vkquake2.vkquake2Generator import VKQuake2Generator
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controllers
    from configgen.types import Resolution


class TestVKQuake2Generator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[VKQuake2Generator]:
        return VKQuake2Generator

    @pytest.fixture
    def fs(self, fs: FakeFilesystem) -> FakeFilesystem:
        fs.create_file('/usr/bin/vkquake2/quake2')
        fs.create_file('/usr/bin/vkquake2/directory/resource.txt')
        fs.create_dir('/userdata/roms/quake2')
        return fs

    @pytest.mark.parametrize(
        ('resolution', 'result'),
        [
            ({'width': 640, 'height': 480}, 4 / 3),
            ({'width': 1920, 'height': 1080}, 16 / 9),
            ({'width': 1920, 'height': 1145}, 4 / 3),
        ],
        ids=str,
    )
    def test_get_in_game_ratio(  # pyright: ignore
        self, generator: VKQuake2Generator, resolution: Resolution, result: bool
    ) -> None:
        assert generator.getInGameRatio(SystemConfig({}), resolution, Path()) == result

    @pytest.mark.parametrize(
        'rom_name',
        [
            'Quake II',
            'Quake II - Ground Zero',
            'Quake II - The Reckoning',
            'Quake II - Zaero',
            'Quake II - Slight Mechanical Destruction',
        ],
    )
    def test_generate(
        self,
        generator: VKQuake2Generator,
        fs: FakeFilesystem,
        rom_name: str,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.Mock(),
                ROMS / 'quake2' / f'{rom_name}.quake2',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )

        assert filecmp.cmp('/usr/bin/vkquake2/quake2', '/userdata/roms/quake2/quake2')
        assert filecmp.cmp('/usr/bin/vkquake2/directory/resource.txt', '/userdata/roms/quake2/directory/resource.txt')
        assert fs.cwd == '/userdata/roms/quake2'

    def test_generate_existing(
        self,
        generator: VKQuake2Generator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
    ) -> None:
        fs.create_file('/userdata/roms/quake2/quake2', contents='newer quake2 bin')
        fs.create_file('/userdata/roms/quake2/directory/resource.txt', contents='newer resource.txt')

        generator.generate(
            mocker.Mock(),
            ROMS / 'quake2' / 'Quake II.quake2',
            one_player_controllers,
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (ROMS / 'quake2' / 'quake2').read_text() == ''
        assert (ROMS / 'quake2' / 'directory' / 'resource.txt').read_text() == ''

    def test_generate_raises(
        self,
        generator: VKQuake2Generator,
        fs: FakeFilesystem,
        one_player_controllers: Controllers,
        mocker: MockerFixture,
    ) -> None:
        fs.remove_object('/usr/bin/vkquake2')

        with pytest.raises(BatoceraException, match=r'^Source directory \/usr\/bin\/vkquake2 does not exist\.$'):
            generator.generate(
                mocker.Mock(),
                ROMS / 'quake2' / 'Quake II.quake2',
                one_player_controllers,
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
