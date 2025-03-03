from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from configgen.batoceraPaths import HOME
from configgen.generators.kodi.kodiGenerator import KodiGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller, Controllers


@pytest.mark.usefixtures('fs')
class TestKodiGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[KodiGenerator]:
        return KodiGenerator

    def test_generate(
        self,
        generator: KodiGenerator,
        mocker: MockerFixture,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        gpio_controller_1: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        assert (
            generator.generate(
                mocker.ANY,
                mocker.ANY,
                make_player_controller_list(generic_xbox_pad, ps3_controller, gpio_controller_1),
                {},
                [],
                {},
                mocker.ANY,
            )
            == snapshot
        )
        assert (
            HOME / '.kodi' / 'userdata' / 'addon_data' / 'peripheral.joystick' / 'settings.xml'
        ).read_text() == snapshot(name='settings.xml')
        assert (HOME / '.kodi' / 'userdata' / 'advancedsettings.xml').read_text() == snapshot(
            name='advancedsettings.xml'
        )
        assert (
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
            / 'batocera_030000005e0400000a0b000005040000_92cd84a75c931635896887ba7718deb0.xml'
        ).read_text() == snapshot(name='xbox pad xml')
        assert (
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
            / 'batocera_030000004c0500006802000011810000_d13b8d6f46331f0e7ce5bac321b9e548.xml'
        ).read_text() == snapshot(name='ps3 controller xml')
        assert (
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
            / 'batocera_15000000010000000100000000010000_fa84aed20bcec70f2fac41764a6932f5.xml'
        ).read_text() == snapshot(name='gpio controller xml')

    def test_generate_existing(
        self,
        generator: KodiGenerator,
        fs: FakeFilesystem,
        mocker: MockerFixture,
        one_player_controllers: Controllers,
    ) -> None:
        fs.create_file(
            HOME / '.kodi' / 'userdata' / 'addon_data' / 'peripheral.joystick' / 'settings.xml', contents='existing'
        )
        fs.create_file(HOME / '.kodi' / 'userdata' / 'advancedsettings.xml', contents='existing')
        fs.create_file(
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
            / 'batocera_030000005e0400000a0b000005040000_92cd84a75c931635896887ba7718deb0.xml',
            contents='existing',
        )

        generator.generate(
            mocker.ANY,
            mocker.ANY,
            one_player_controllers,
            {},
            [],
            {},
            mocker.ANY,
        )
        assert (
            HOME / '.kodi' / 'userdata' / 'addon_data' / 'peripheral.joystick' / 'settings.xml'
        ).read_text() != 'existing'
        assert (HOME / '.kodi' / 'userdata' / 'advancedsettings.xml').read_text() == 'existing'
        assert (
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
            / 'batocera_030000005e0400000a0b000005040000_92cd84a75c931635896887ba7718deb0.xml'
        ).read_text() != 'existing'

    def test_generate_no_controllers(
        self,
        generator: KodiGenerator,
        mocker: MockerFixture,
    ) -> None:
        generator.generate(
            mocker.ANY,
            mocker.ANY,
            [],
            {},
            [],
            {},
            mocker.ANY,
        )
        assert not (HOME / '.kodi' / 'userdata' / 'addon_data' / 'peripheral.joystick' / 'settings.xml').exists()
        assert not (HOME / '.kodi' / 'userdata' / 'advancedsettings.xml').exists()
        assert not (
            HOME
            / '.kodi'
            / 'userdata'
            / 'addon_data'
            / 'peripheral.joystick'
            / 'resources'
            / 'buttonmaps'
            / 'xml'
            / 'udev'
        ).exists()
