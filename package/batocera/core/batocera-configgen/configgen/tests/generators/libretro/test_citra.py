from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
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


@pytest.mark.core('citra')
class TestLibretroGeneratorCitra(LibretroBaseCoreTest):
    def test_generate(self, generator, default_extension, fs, mock_system, snapshot) -> None:
        super().test_generate(generator, default_extension, fs, mock_system, snapshot)

        assert Path(CONFIGS / 'retroarch' / '3ds.cfg').read_text() == snapshot(name='3ds.cfg')

    def test_generate_existing_3ds_cfg(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        fs.create_file(CONFIGS / 'retroarch' / '3ds.cfg', contents='existing 3ds.cfg')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        assert Path(CONFIGS / 'retroarch' / '3ds.cfg').read_text() == 'existing 3ds.cfg'

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

        fs.create_file(ROMS / '3ds' / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / '3ds' / f'rom.{default_extension}',
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
