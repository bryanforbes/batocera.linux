from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('yabasanshiro')
class TestLibretroGeneratorYabasanshiro(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'resolution_mode': '2x'},
            {'multitap_yabasanshiro': ['disabled', 'port1', 'port2', 'port12']},
            {'controller1_saturn': '5'},
            {'controller2_saturn': '5'},
            {'yabasanshiro_language': 'spanish'},
        ],
    )
    def test_generate_core_config(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        return super().test_generate_core_config(generator, default_extension, fs, mock_system, snapshot)

    def test_generate_controllers_config(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, ps3_controller, keyboard_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)
