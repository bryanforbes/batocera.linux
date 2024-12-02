from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import ROMS
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.core('melonds')
class TestLibretroGeneratorMelonDS(LibretroBaseCoreTest):
    @pytest.mark.parametrize_core_configs(
        [
            {'melonds_console_mode': 'DSi'},
            {'melonds_boot_directly': 'disabled'},
            {'melonds_use_fw_settings': 'enable'},
            {'melonds_language': 'French'},
            {
                'melonds_screen_layout': [
                    'Hybrid Top-Ratio2',
                    'Hybrid Top-Ratio3',
                    'Hybrid Bottom-Ratio2',
                    'Hybrid Bottom-Ratio3',
                    'Bottom/Top',
                ]
            },
            {'melonds_touch_mode': 'Mouse'},
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
        mocker: MockFixture,
        get_devices_information: Mock,
        get_associated_mouse: Mock,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        get_devices_information.return_value = mocker.sentinel.devices_information
        get_associated_mouse.side_effect = [1, None]

        fs.create_file(ROMS / 'nds' / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / 'nds' / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, ps3_controller),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)
        assert get_associated_mouse.call_args_list == [
            mocker.call(mocker.sentinel.devices_information, '/dev/input/event1'),
            mocker.call(mocker.sentinel.devices_information, '/dev/input/event2'),
        ]
