from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.generators.cemu.cemuPaths import CEMU_CONFIG

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import ControllerMapping
    from configgen.Emulator import Emulator


@pytest.mark.usefixtures(
    'vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_uuid', 'os_environ_lang'
)
class TestCemuGenerator:
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

    def test_get_hotkeys_context(self, snapshot: SnapshotAssertion) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        assert CemuGenerator().getHotkeysContext() == snapshot

    def test_has_internal_mango_hud_call(self) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        assert CemuGenerator().hasInternalMangoHUDCall()

    @pytest.mark.parametrize(
        ('mock_system_config', 'result'),
        [({}, False), ({'cemu_touchpad': '0'}, False), ({'cemu_touchpad': '1'}, True)],
        ids=str,
    )
    def test_get_mouse_mode(self, mock_system_config: dict[str, Any], result: bool) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        assert CemuGenerator().getMouseMode(mock_system_config, '') == result

    def test_generate(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        command = CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot
        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_squashfs(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/tmp/rom/code/foo.rpx')
        fs.create_file('/tmp/rom/code/bar.rpx')

        command = CemuGenerator().generate(
            mock_system,
            '/tmp/rom',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot

    def test_generate_rom_config(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        command = CemuGenerator().generate(
            mock_system,
            'config',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (command.array, command.env) == snapshot

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
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')

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
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_existing(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')
        fs.create_file(
            CEMU_CONFIG / 'settings.xml',
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

        CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_existing_unparseable(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
    ) -> None:
        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')
        fs.create_file(CEMU_CONFIG / 'settings.xml', contents='foo')

        CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')

    def test_generate_vulkan(
        self,
        fs: FakeFilesystem,
        mock_system: Emulator,
        one_player_controllers: ControllerMapping,
        snapshot: SnapshotAssertion,
        vulkan_is_available: Mock,
        vulkan_has_discrete_gpu: Mock,
        vulkan_get_discrete_gpu_uuid: Mock,
    ) -> None:
        vulkan_is_available.return_value = True
        vulkan_has_discrete_gpu.return_value = True
        vulkan_get_discrete_gpu_uuid.return_value = 'UUID'

        from configgen.generators.cemu.cemuGenerator import CemuGenerator

        fs.create_file('/userdata/roms/cemu/rom.wua', contents='rom.wua')

        CemuGenerator().generate(
            mock_system,
            '/userdata/roms/cemu/rom.wua',
            one_player_controllers,
            {},
            {},
            {},
            {},  # pyright: ignore
        )

        assert (CEMU_CONFIG / 'settings.xml').read_text() == snapshot(name='settings.xml')
