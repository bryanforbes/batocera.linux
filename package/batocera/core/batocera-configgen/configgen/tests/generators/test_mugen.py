from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from configgen.config import SystemConfig
from configgen.generators.mugen.mugenGenerator import MugenGenerator
from tests.conftest import get_os_environ
from tests.generators.base import GeneratorBaseTest

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs', 'subprocess_run')
class TestMugenGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[MugenGenerator]:
        return MugenGenerator

    @pytest.fixture(autouse=True)
    def os_environ_nvidia(self, mocker: MockerFixture) -> None:
        mocker.patch.dict(
            'os.environ',
            values={
                '__VK_LAYER_NV_optimus': '1',
                'FOO': 'BAR',
                '__NV_PRIME_RENDER_OFFLOAD': '1',
                '__GLX_VENDOR_LIBRARY_NAME': '1',
            },
            clear=True,
        )

    def test_get_in_game_ratio(self, generator: MugenGenerator) -> None:  # pyright: ignore
        assert generator.getInGameRatio(SystemConfig({}), {'width': 0, 'height': 0}, Path()) == 16 / 9

    def test_generate(
        self,
        generator: MugenGenerator,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        snapshot: SnapshotAssertion,
        subprocess_run: Mock,
    ) -> None:
        fs.create_file(
            ROMS / 'mugen' / 'rom.pc' / 'data' / 'mugen.cfg',
            encoding='utf-8-sig',
            contents=""";-=====================================================-
;        Configuration file for M.U.G.E.N
;-=====================================================-
; Game options configurable in M.U.G.E.N's options screen go here.
; Does not include key config.
[Options]
; Basic options
Difficulty = 8
Life = 350
Time = 120
GameSpeed = 0

; Team-only config
Team.1VS2Life = 150
Team.LoseOnKO = 0

;-------------------------------------------------------
[Config]
 ;Set the game speed here. The default is 60 frames per second. The
 ;larger the number, the faster it goes. Don't use a value less than 10.
GameSpeed = 60

 ;Game native width and height.
 ;Recommended settings are:
 ;  640x480   Standard definition 4:3
 ; 1280x720   High definition 16:9
 ; 1920x1080  Full HD 16:9
GameWidth = 1280
GameHeight = 720
""",
        )

        assert (
            generator.generate(
                mocker.ANY,
                ROMS / 'mugen' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (ROMS / 'mugen' / 'rom.pc' / 'data' / 'mugen.cfg').read_text() == snapshot(name='config')
        assert subprocess_run.call_args_list == snapshot(name='settings-set')

    def test_generate_nvidia(
        self, generator: MugenGenerator, fs: FakeFilesystem, mocker: MockerFixture, snapshot: SnapshotAssertion
    ) -> None:
        fs.create_file('/var/tmp/nvidia.prime')
        fs.create_file(ROMS / 'mugen' / 'rom.pc' / 'data' / 'mugen.cfg')

        assert (
            generator.generate(
                mocker.ANY,
                ROMS / 'mugen' / 'rom.pc',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert get_os_environ() == snapshot(name='environ')
