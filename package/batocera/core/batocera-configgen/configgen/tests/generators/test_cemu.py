from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.config import SystemConfig
from configgen.generators.cemu.cemuGenerator import CemuGenerator
from tests.generators.base import GeneratorBaseTest
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@pytest.mark.usefixtures(
    'vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_uuid', 'os_environ_lang'
)
class TestCemuGenerator(GeneratorBaseTest):
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return CemuGenerator

    @pytest.fixture
    def system_name(self) -> str:
        return 'wiiu'

    @pytest.fixture
    def emulator(self) -> str:
        return 'cemu'

    @pytest.fixture(autouse=True)
    def get_audio_device(self, mocker: MockerFixture) -> Mock:
        run = mocker.patch('subprocess.run')
        proc = mocker.Mock()
        proc.stdout = b'/dev/audio-device'
        run.return_value = proc
        return run

    def test_has_internal_mangohud_call(self, generator: Generator) -> None:
        assert generator.hasInternalMangoHUDCall()

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, False), ({'cemu_touchpad': '0'}, False), ({'cemu_touchpad': '1'}, True)],
        ids=str,
    )
    def test_get_mouse_mode(  # pyright: ignore
        self, generator: Generator, mock_system_config: dict[str, Any], result: bool
    ) -> None:
        assert generator.getMouseMode(SystemConfig(mock_system_config), Path()) == result

    def test_generate(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'cemu' / 'rom.wua',
                [],
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )
        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_squashfs(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/tmp/rom/code/foo.rpx')
        fs.create_file('/tmp/rom/code/bar.rpx')

        assert (
            generator.generate(
                mock_system,
                Path('/tmp/rom'),
                [],
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    def test_generate_rom_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        assert (
            generator.generate(
                mock_system,
                Path('config'),
                [],
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cemu_gamepad': 'True'},
            {'cemu_gamepad': 'False'},
            {'cemu_gfxbackend': '2'},
            {'cemu_gfxbackend': '1'},
            {'cemu_async': 'False'},
            {'cemu_async': 'True'},
            {'cemu_vsync': '1'},
            {'cemu_upscale': '1'},
            {'cemu_downscale': '1'},
            {'cemu_aspect': '1'},
            {'cemu_overlay': 'True'},
            {'cemu_overlay': 'False'},
            {'cemu_notifications': 'True'},
            {'cemu_notifications': 'False'},
            {'cemu_audio_channels': '2'},
            {'cemu_audio_config': '1'},
            {'cemu_audio_config': '0'},
            {'cemu_console_language': 'ui'},
            {'cemu_console_language': 'ja_JP'},
        ],
        ids=str,
    )
    def test_generate_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            [],
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')

    @pytest.mark.parametrize(
        'os_environ_lang',
        [
            None,
            'ja_JP',
            'en_US',
            'fr_FR',
            'de_DE',
            'it_IT',
            'es_ES',
            'zh_CN',
            'ko_KR',
            'nl_NL',
            'pt_PT',
            'ru_RU',
            'zh_TW',
            'en_GB',
        ],
        indirect=True,
    )
    def test_generate_lang(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            [],
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_existing(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')
        fs.create_file(
            CONFIGS / 'cemu' / 'settings.xml',
            contents="""<?xml version="1.0" ?>
<content>
	<mlc_path>/userdata/saves/wiiu</mlc_path>
	<check_update>false</check_update>
	<gp_download>true</gp_download>
	<logflag>0</logflag>
	<advanced_ppc_logging>false</advanced_ppc_logging>
	<use_discord_presence>false</use_discord_presence>
	<fullscreen_menubar>false</fullscreen_menubar>
	<vk_warning>false</vk_warning>
	<fullscreen>true</fullscreen>
	<console_language>1</console_language>
	<window_position>
		<x>0</x>
		<y>0</y>
	</window_position>
	<window_size>
		<x>640</x>
		<y>480</y>
	</window_size>
	<open_pad>false</open_pad>
	<pad_position>
		<x>0</x>
		<y>0</y>
	</pad_position>
	<pad_size>
		<x>640</x>
		<y>480</y>
	</pad_size>
	<GamePaths>
		<Entry>/userdata/roms/wiiu</Entry>
	</GamePaths>
	<Graphic>
		<api>0</api>
		<AsyncCompile>true</AsyncCompile>
		<VSync>0</VSync>
		<UpscaleFilter>2</UpscaleFilter>
		<DownscaleFilter>0</DownscaleFilter>
		<FullscreenScaling>1</FullscreenScaling>
		<Overlay>
			<Position>3</Position>
			<TextColor>4294967295</TextColor>
			<TextScale>100</TextScale>
			<FPS>false</FPS>
			<DrawCalls>false</DrawCalls>
			<CPUUsage>false</CPUUsage>
			<CPUPerCoreUsage>false</CPUPerCoreUsage>
			<RAMUsage>false</RAMUsage>
			<VRAMUsage>false</VRAMUsage>
		</Overlay>
		<Notification>
			<Position>1</Position>
			<TextColor>4294967295</TextColor>
			<TextScale>100</TextScale>
			<ControllerProfiles>false</ControllerProfiles>
			<ControllerBattery>false</ControllerBattery>
			<ShaderCompiling>false</ShaderCompiling>
			<FriendService>false</FriendService>
		</Notification>
	</Graphic>
	<Audio>
		<api>3</api>
		<TVChannels>1</TVChannels>
		<TVVolume>100</TVVolume>
		<TVDevice>/dev/audio-device</TVDevice>
	</Audio>
</content>
""",
        )
        fs.create_file(CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            [],
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')
        assert not (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml').exists()

    def test_generate_existing_unparseable(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')
        fs.create_file(CONFIGS / 'cemu' / 'settings.xml', contents='foo')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            [],
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')

    @pytest.mark.parametrize(
        ('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_uuid'),
        [
            pytest.param(False, False, None, id='vulkan unavailable'),
            pytest.param(True, False, None, id='vulkan available, no discrete gpu'),
            pytest.param(True, True, None, id='vulkan available, no discrete gpu UUID'),
            pytest.param(True, True, 'UUID', id='vulkan available'),
        ],
        indirect=True,
    )
    def test_generate_vulkan(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            [],
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_controllers(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        assert (
            generator.generate(
                mock_system,
                ROMS / 'cemu' / 'rom.wua',
                make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
                {},
                [],
                {},
                {},  # pyright: ignore
            )
            == snapshot
        )

        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml').read_text() == snapshot(
            name='controller0.xml'
        )
        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller1.xml').read_text() == snapshot(
            name='controller1.xml'
        )
        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller2.xml').read_text() == snapshot(
            name='controller2.xml'
        )

    @pytest.mark.parametrize(
        'mock_system_config',
        [
            {'cemu_controller_combination': '0'},
            {'cemu_controller_combination': '1'},
            {'cemu_controller_combination': '2'},
            {'cemu_controller_combination': '3'},
            {'cemu_controller_combination': '4'},
            {'cemu_rumble': '0.25'},
        ],
        ids=str,
    )
    def test_generate_controllers_config(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            make_player_controller_list(generic_xbox_pad, ps3_controller, generic_xbox_pad),
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml').read_text() == snapshot(
            name='controller0.xml'
        )
        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller1.xml').read_text() == snapshot(
            name='controller1.xml'
        )
        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller2.xml').read_text() == snapshot(
            name='controller2.xml'
        )

    @pytest.mark.mock_system_config({'cemu_controller_combination': '3'})
    @pytest.mark.parametrize('motion_plus', [True, False], ids=['motion plus', 'plain'])
    @pytest.mark.parametrize(
        'names',
        [
            pytest.param(['Nintendo Wii Remote Classic Controller', 'Nintendo Wii Remote Nunchuk'], id='nunchuk'),
            pytest.param(['Nintendo Wii Remote Classic Controller'], id='classic controller'),
            pytest.param([], id='remote only'),
        ],
    )
    def test_generate_controllers_wiimotes(
        self,
        generator: Generator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        mock_system: Emulator,
        wiimote: Controller,
        motion_plus: bool,
        snapshot: SnapshotAssertion,
        pyudev: Mock,
        names: list[str],
    ) -> None:
        context_instance = mocker.Mock()
        device_instance = mocker.Mock()
        list_devices_value = mocker.Mock()

        context_instance.list_devices.return_value = list_devices_value
        list_devices_value.match_subsystem.return_value = [
            mocker.Mock(properties={} if name is None else {'NAME': name})
            for name in [*names, None, 'Foo', 'Nintendo Wii Remote' + (' Motion Plus' if motion_plus else '')]
        ]

        pyudev.Context.return_value = context_instance
        pyudev.Devices.from_device_file.return_value = device_instance

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        controllers = make_player_controller_list(wiimote, wiimote)
        for controller in controllers:
            controller.real_name = controller.name

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml').read_text() == snapshot(
            name='controller0.xml'
        )

    @pytest.mark.mock_system_config({'cemu_controller_combination': '1'})
    @pytest.mark.parametrize('motion_plus', [True, False], ids=['motion plus', 'plain'])
    @pytest.mark.parametrize(
        'names',
        [
            pytest.param(['Nintendo Wii Remote Classic Controller', 'Nintendo Wii Remote Nunchuk'], id='nunchuk'),
            pytest.param(['Nintendo Wii Remote Classic Controller'], id='classic controller'),
            pytest.param([], id='remote only'),
        ],
    )
    def test_generate_controllers_gamepad_wiimotes(
        self,
        generator: Generator,
        mocker: MockerFixture,
        fs: FakeFilesystem,
        mock_system: Emulator,
        wiimote: Controller,
        generic_xbox_pad: Controller,
        motion_plus: bool,
        snapshot: SnapshotAssertion,
        pyudev: Mock,
        names: list[str],
    ) -> None:
        context_instance = mocker.Mock()
        device_instance = mocker.Mock()
        list_devices_value = mocker.Mock()

        context_instance.list_devices.return_value = list_devices_value
        list_devices_value.match_subsystem.return_value = [
            mocker.Mock(properties={} if name is None else {'NAME': name})
            for name in [*names, None, 'Foo', 'Nintendo Wii Remote' + (' Motion Plus' if motion_plus else '')]
        ]

        pyudev.Context.return_value = context_instance
        pyudev.Devices.from_device_file.return_value = device_instance

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        controllers = make_player_controller_list(generic_xbox_pad, wiimote)
        for controller in controllers:
            controller.real_name = controller.name

        generator.generate(
            mock_system,
            ROMS / 'cemu' / 'rom.wua',
            controllers,
            {},
            [],
            {},
            {},  # pyright: ignore
        )

        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller0.xml').read_text() == snapshot(
            name='controller0.xml'
        )
        assert (CONFIGS / 'cemu' / 'controllerProfiles' / 'controller1.xml').read_text() == snapshot(
            name='controller1.xml'
        )
