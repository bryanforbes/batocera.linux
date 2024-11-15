from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ... import controllersConfig
from ...batoceraPaths import BIOS, ROMS, ensure_parents_and_open
from ...gun import GunMapping, guns_need_crosses
from ...utils.configparser import CaseSensitiveConfigParser
from .libretroPaths import RETROARCH_CONFIG

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from ...Emulator import Emulator
    from ...settings.unixSettings import UnixSettings
    from ...types import DeviceInfoMapping


def _set(settings: UnixSettings, settings_name: str, value: Any) -> None:
    settings.save(settings_name, f'"{value}"')


def _set_from_system(settings: UnixSettings, settings_name: str, system: Emulator, option_name: str | None = None, *, default: Any = '') -> None:
    _set(settings, settings_name, system.get_option(option_name or settings_name, default))


def _cap32_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Amstrad CPC / GX4000

    # Virtual Keyboard by default (select+start) change to (start+Y)
    _set(coreSettings, 'cap32_combokey', 'y')
    # Auto Select Model
    if (system.name == 'gx4000'):
        _set(coreSettings, 'cap32_model', '6128+ (experimental)')
    else:
        _set_from_system(coreSettings, 'cap32_model', system, default='6128')
    # Ram size
    _set_from_system(coreSettings, 'cap32_ram', system, default="128")
    # colour depth
    _set_from_system(coreSettings, 'cap32_gfx_colors', system, "cap32_colour", default="24bit")
    # language
    _set_from_system(coreSettings, 'cap32_lang_layout', system, "cap32_language", default="english")


def _atari8000_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Atari 800 and 5200

    if (system.name == 'atari800'):
        # Select Atari 800
        # Let user overide Atari System
        _set_from_system(coreSettings, 'atari800_system', system, default="800XL (64K)")
        # Video Standard
        _set_from_system(coreSettings, 'atari800_ntscpal', system, default="NTSC")
        # SIO Acceleration
        _set_from_system(coreSettings, 'atari800_sioaccel', system, default="enabled")
        # Hi-Res Artifacting
        _set_from_system(coreSettings, 'atari800_artifacting', system, default="disabled")
        # Internal resolution
        _set_from_system(coreSettings, 'atari800_resolution', system) # Default : 336x240
        # Internal BASIC interpreter
        _set_from_system(coreSettings, 'atari800_internalbasic', system, default="disabled")

        # WARNING: Now we must stop to use "atari800.cfg" because core options crush them

    else:
        # Select Atari 5200
        _set(coreSettings, 'atari800_system', '5200')
        # Autodetect A5200 CartType (Off/On)
        _set(coreSettings, 'atari800_CartType', 'enabled')
        # Joy Hack (for robotron)
        _set_from_system(coreSettings, 'atari800_opt2', system, default="disabled")


def _virtualjaguar_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Atari Jaguar

    # Fast Blitter (Older, Faster, Less compatible)
    _set_from_system(coreSettings, 'virtualjaguar_usefastblitter', system, 'usefastblitter', default="enabled")
    # Show Bios Bootlogo
    _set_from_system(coreSettings, 'virtualjaguar_bios', system, 'bios_vj', default="enabled")
    # Doom Res Hack
    _set_from_system(coreSettings, 'virtualjaguar_doom_res_hack', system, 'doom_res_hack', default="disabled")


def _handy_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Atari Lynx

    # Display rotation
    # Set this option to start game at 'None' because it crash the emulator
    _set(coreSettings, 'handy_rot', 'None')


def _commodore_64_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore 64

    # Activate Jiffydos
    _set(coreSettings, 'vice_jiffydos',          'enabled')
    # Enable Automatic Load Warp
    _set(coreSettings, 'vice_autoloadwarp',      'enabled')
    # Disable Datasette Hotkeys
    _set(coreSettings, 'vice_datasette_hotkeys', 'disabled')
    # Not Read 'vicerc'
    _set(coreSettings, 'vice_read_vicerc',       'disabled')
    # Select Joystick Type
    _set(coreSettings, 'vice_Controller',        'joystick')
    # Disable Turbo Fire
    _set(coreSettings, 'vice_turbo_fire',        'disabled')
    # Controller options for c64 are in libretroControllers.py
    c64_mapping = { 'a': "---",
            'aspect_ratio_toggle': "---",
            'b': "---",
            'joyport_switch': "RETROK_F10",
            'l': "RETROK_ESCAPE",
            'l2': "RETROK_F11",
            'l3': "SWITCH_JOYPORT",
            'ld': "---",
            'll': "---",
            'lr': "---",
            'lu': "---",
            'r': "RETROK_PAGEUP",
            'r2': "RETROK_LSHIFT",
            'rd': "RETROK_F7",
            'reset': "---",
            'rl': "RETROK_F3",
            'rr': "RETROK_F5",
            'ru': "RETROK_F1",
            'select': "TOGGLE_VKBD",
            'start': "RETROK_RETURN",
            'statusbar': "RETROK_F9",
            'vkbd': "RETROK_F12",
            'warp_mode': "RETROK_F11",
            'turbo_fire_toggle': "RETROK_RCTRL",
            'x': "RETROK_RCTRL",
            'y': "RETROK_SPACE" }
    for key, mapped_key in c64_mapping.items():
        _set(coreSettings, 'vice_mapper_' + key, mapped_key)

    # Model type
    _set_from_system(coreSettings, 'vice_c64_model', system, 'c64_model', default="C64 PAL auto")
    # Aspect Ratio
    _set_from_system(coreSettings, 'vice_aspect_ratio', system, default="pal")
    # Zoom Mode
    if (zoom_mode := system.get_option('vice_zoom_mode')) is not system.MISSING:
        if zoom_mode == 'automatic':
            _set(coreSettings, 'vice_crop', 'auto')
        else:
            _set(coreSettings, 'vice_crop', zoom_mode)
    else:
        _set(coreSettings, 'vice_crop', 'auto_disable')
    _set(coreSettings, 'vice_zoom_mode', 'deprecated')
    # External palette
    _set_from_system(coreSettings, 'vice_external_palette', system, default="colodore")
    # Button options
    _set_from_system(coreSettings, 'vice_retropad_options', system, default="jump")
    # Select Controller Port
    _set_from_system(coreSettings, 'vice_joyport', system, default="2")
    # Select Controller Type
    # gun
    if system.get_option_bool('use_guns') and guns:
        _set(coreSettings, 'vice_joyport_type', '14')
    else:
        _set_from_system(coreSettings, 'vice_joyport_type', system, default="1")
    # RAM Expansion Unit (REU)
    _set_from_system(coreSettings, 'vice_ram_expansion_unit', system, default="none")
    # Keyboard Pass-through for Pad2Key
    _set_from_system(coreSettings, 'vice_physical_keyboard_pass_through', system, 'vice_keyboard_pass_through', default="disabled")


def _commodore_128_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore 128

    # Activate Jiffydos
    _set(coreSettings, 'vice_jiffydos',          'enabled')
    # Enable Automatic Load Warp
    _set(coreSettings, 'vice_autoloadwarp',      'enabled')
    # Disable Datasette Hotkeys
    _set(coreSettings, 'vice_datasette_hotkeys', 'disabled')
    # Not Read 'vicerc'
    _set(coreSettings, 'vice_read_vicerc',       'disabled')
    # Select Joystick Type
    _set(coreSettings, 'vice_Controller',        'joystick')
    # Disable Turbo Fire
    _set(coreSettings, 'vice_turbo_fire',        'disabled')

    # Model type
    _set_from_system(coreSettings, 'vice_c128_model', system, 'c128_model', default="C128 PAL")
    # Aspect Ratio
    _set_from_system(coreSettings, 'vice_aspect_ratio', system, default="pal")
    # Zoom Mode
    if (zoom_mode := system.get_option('vice_zoom_mode')) is not system.MISSING:
        if zoom_mode == 'automatic':
            _set(coreSettings, 'vice_crop', 'auto')
        else:
            _set(coreSettings, 'vice_crop', zoom_mode)
    else:
        _set(coreSettings, 'vice_crop', 'auto_disable')
    _set(coreSettings, 'vice_zoom_mode', 'deprecated')
    # External palette
    _set_from_system(coreSettings, 'vice_external_palette', system, default="colodore")
    # Button options
    _set_from_system(coreSettings, 'vice_retropad_options', system, default="disabled")
    # Select Controller Port
    _set_from_system(coreSettings, 'vice_joyport', system, default="2")
    # Select Controller Type
    _set_from_system(coreSettings, 'vice_joyport_type', system, default="1")
    # Keyboard Pass-through for Pad2Key
    _set_from_system(coreSettings, 'vice_physical_keyboard_pass_through', system, 'vice_keyboard_pass_through', default="disabled")


def _commodore_plus_4_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore Plus/4

    # Enable Automatic Load Warp
    _set(coreSettings, 'vice_autoloadwarp',      'enabled')
    # Disable Datasette Hotkeys
    _set(coreSettings, 'vice_datasette_hotkeys', 'disabled')
    # Not Read 'vicerc'
    _set(coreSettings, 'vice_read_vicerc',       'disabled')
    # Select Joystick Type
    _set(coreSettings, 'vice_Controller',        'joystick')
    # Disable Turbo Fire
    _set(coreSettings, 'vice_turbo_fire',        'disabled')

    # Model type
    _set_from_system(coreSettings, 'vice_plus4_model', system, 'plus4_model', default="PLUS4 PAL")
    # Aspect Ratio
    _set_from_system(coreSettings, 'vice_aspect_ratio', system, default="pal")
    # Zoom Mode
    if (zoom_mode := system.get_option('vice_zoom_mode')) is not system.MISSING:
        if zoom_mode == 'automatic':
            _set(coreSettings, 'vice_crop', 'auto')
        else:
            _set(coreSettings, 'vice_crop', zoom_mode)
    else:
        _set(coreSettings, 'vice_crop', 'auto_disable')
    _set(coreSettings, 'vice_zoom_mode', 'deprecated')
    # External palette
    _set_from_system(coreSettings, 'vice_plus4_external_palette', system, default="colodore_ted")
    # Button options
    _set_from_system(coreSettings, 'vice_retropad_options', system, default="disabled")
    # Select Controller Port
    _set_from_system(coreSettings, 'vice_joyport', system, default="2")
    # Select Controller Type
    _set_from_system(coreSettings, 'vice_joyport_type', system, default="1")
    # Keyboard Pass-through for Pad2Key
    _set_from_system(coreSettings, 'vice_physical_keyboard_pass_through', system, 'vice_keyboard_pass_through', default="disabled")


def _commodore_vic_20_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore VIC-20

    # Enable Automatic Load Warp
    _set(coreSettings, 'vice_autoloadwarp',      'enabled')
    # Disable Datasette Hotkeys
    _set(coreSettings, 'vice_datasette_hotkeys', 'disabled')
    # Not Read 'vicerc'
    _set(coreSettings, 'vice_read_vicerc',       'disabled')
    # Select Joystick Type
    _set(coreSettings, 'vice_Controller',        'joystick')
    # Disable Turbo Fire
    _set(coreSettings, 'vice_turbo_fire',        'disabled')

    # Model type
    _set_from_system(coreSettings, 'vice_vic20_model', system, 'vic20_model', default="VIC20 PAL auto")
    # Aspect Ratio
    _set_from_system(coreSettings, 'vice_aspect_ratio', system, default="pal")
    # Zoom Mode
    if (zoom_mode := system.get_option('vice_zoom_mode')) is not system.MISSING:
        if zoom_mode == 'automatic':
            _set(coreSettings, 'vice_crop', 'auto')
        else:
            _set(coreSettings, 'vice_crop', zoom_mode)
    else:
        _set(coreSettings, 'vice_crop', 'auto_disable')
    _set(coreSettings, 'vice_zoom_mode', 'deprecated')
    # External palette
    _set_from_system(coreSettings, 'vice_vic20_external_palette', system, default="colodore_vic")
    # Button options
    _set_from_system(coreSettings, 'vice_retropad_options', system, default="disabled")
    # Select Controller Port
    _set_from_system(coreSettings, 'vice_joyport', system, default="2")
    # Select Controller Type
    _set_from_system(coreSettings, 'vice_joyport_type', system, default="1")
    # Keyboard Pass-through for Pad2Key
    _set_from_system(coreSettings, 'vice_physical_keyboard_pass_through', system, 'vice_keyboard_pass_through', default="disabled")


def _commodore_pet_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore PET

    # Enable Automatic Load Warp
    _set(coreSettings, 'vice_autoloadwarp',      'enabled')
    # Disable Datasette Hotkeys
    _set(coreSettings, 'vice_datasette_hotkeys', 'disabled')
    # Not Read 'vicerc'
    _set(coreSettings, 'vice_read_vicerc',       'disabled')
    # Select Joystick Type
    _set(coreSettings, 'vice_Controller',        'joystick')
    # Disable Turbo Fire
    _set(coreSettings, 'vice_turbo_fire',        'disabled')

    # Model type
    _set_from_system(coreSettings, 'vice_pet_model', system, 'pet_model', default="8032")
    # Aspect Ratio
    _set_from_system(coreSettings, 'vice_aspect_ratio', system, default="pal")
    # Zoom Mode
    if (zoom_mode := system.get_option('vice_zoom_mode')) is not system.MISSING:
        if zoom_mode == 'automatic':
            _set(coreSettings, 'vice_crop', 'auto')
        else:
            _set(coreSettings, 'vice_crop', zoom_mode)
    else:
        _set(coreSettings, 'vice_crop', 'auto_disable')
    _set(coreSettings, 'vice_zoom_mode', 'deprecated')
    # External palette
    _set_from_system(coreSettings, 'vice_pet_external_palette', system, default="default")
    # Button options
    _set_from_system(coreSettings, 'vice_retropad_options', system, default="disabled")
    # Select Controller Port
    _set_from_system(coreSettings, 'vice_joyport', system, default="2")
    # Select Controller Type
    _set_from_system(coreSettings, 'vice_joyport_type', system, default="1")
    # Keyboard Pass-through for Pad2Key
    _set_from_system(coreSettings, 'vice_physical_keyboard_pass_through', system, 'vice_keyboard_pass_through', default="disabled")


def _commodore_amiga_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Commodore AMIGA

    # Functional mapping for Amiga system
    # If you want to change them, you can add
    # some strings to batocera.conf by using
    # this syntax: SYSTEMNAME.retroarchcore.puae_mapper_BUTTONNAME=VALUE
    if system.name != 'amigacd32' and system.get_option('controller1_puae', '517') != '517' and system.get_option('controller2_puae', '517') != '517':
        # Controller mapping for A500 and A1200
        uae_mapping = { 'aspect_ratio_toggle': "---",
            'mouse_toggle': "RETROK_RCTRL",
            'statusbar': "RETROK_F11",
            'vkbd': "---",
            'reset': "---",
            'crop_toggle': "RETROK_F12",
            'zoom_mode_toggle': "---",
            'a': "---",
            'b': "---",
            'x': "RETROK_LALT",
            'y': "RETROK_SPACE",
            'l': "RETROK_ESCAPE",
            'l2': "MOUSE_LEFT_BUTTON",
            'l3': "SWITCH_JOYMOUSE",
            'ld': "---",
            'll': "---",
            'lr': "---",
            'lu': "---",
            'r': "RETROK_F1",
            'r2': "MOUSE_RIGHT_BUTTON",
            'r3': "TOGGLE_STATUSBAR",
            'rd': "---",
            'rl': "---",
            'rr': "---",
            'ru': "---",
            'select': "TOGGLE_VKBD",
            'start': "RETROK_RETURN",}
        for key, mapped_key in uae_mapping.items():
            _set(coreSettings, 'puae_mapper_' + key, mapped_key)
    else:
        # Controller mapping for CD32
        uae_mapping = { 'aspect_ratio_toggle': "---",
            'mouse_toggle': "RETROK_RCTRL",
            'statusbar': "RETROK_F11",
            'vkbd': "---",
            'reset': "---",
            'crop_toggle': "RETROK_F12",
            'zoom_mode_toggle': "---",
            'a': "---",
            'b': "---",
            'x': "---",
            'y': "---",
            'l': "---",
            'l2': "MOUSE_LEFT_BUTTON",
            'l3': "SWITCH_JOYMOUSE",
            'ld': "---",
            'll': "---",
            'lr': "---",
            'lu': "---",
            'r': "---",
            'r2': "MOUSE_RIGHT_BUTTON",
            'r3': "TOGGLE_STATUSBAR",
            'rd': "---",
            'rl': "---",
            'rr': "---",
            'ru': "---",
            'select': "---",
            'start': "---",}
        for key, value in uae_mapping.items():
            _set(coreSettings, 'puae_mapper_' + key, value)
    # Show Video Options
    _set(coreSettings, 'puae_video_options_display', 'enabled')
    # Amiga Model
    if (model := system.get_option('puae_model')) and model != 'automatic':
        _set(coreSettings, 'puae_model', model)
    else:
        if system.name == 'amiga1200':
            _set(coreSettings, 'puae_model', 'A1200')
        elif system.name == 'amigacd32':
            _set(coreSettings, 'puae_model', 'CD32FR')
        elif system.name == 'amigacdtv':
            _set(coreSettings, 'puae_model', 'CDTV')
        else:
            # Will default to A500 when booting floppy disks, A600 when booting hard drives
            _set(coreSettings, 'puae_model', 'auto')

    # CPU Compatibility
    _set_from_system(coreSettings, 'puae_cpu_compatibility', system, 'cpu_compatibility', default="normal")
    # CPU Multiplier (Overclock)
    _set_from_system(coreSettings, 'puae_cpu_throttle', system, 'cpu_throttle', default="0.0")
    _set(coreSettings, 'puae_cpu_multiplier', '0')
    # CPU Cycle Exact Speed (Overclock)
    if system.get_option('cpu_compatibility') == 'exact':
        _set(coreSettings, 'puae_cpu_throttle', '0.0')
        _set_from_system(coreSettings, 'puae_cpu_multiplier', system, 'cpu_multiplier', default="0")
    # Standard Video
    _set_from_system(coreSettings, 'puae_video_standard', system, 'video_standard', default="PAL auto")
    # Video Resolution
    _set_from_system(coreSettings, 'puae_video_resolution', system, 'video_resolution', default="hires")
    # Zoom Mode
    if (zoom_mode := system.get_option('zoom_mode', 'automatic')) != 'automatic':
        _set(coreSettings, 'puae_crop', zoom_mode)
    else:
        _set(coreSettings, 'puae_crop', 'auto')
    _set(coreSettings, 'puae_zoom_mode', 'deprecated')
    # Frameskip
    _set_from_system(coreSettings, 'puae_gfx_framerate', system, 'gfx_framerate', default="disabled")
    # Mouse Speed
    _set_from_system(coreSettings, 'puae_mouse_speed', system, 'mouse_speed', default="200")
    # Jump on B
    if (pad_options := system.get_option('pad_options')) is not system.MISSING:
        _set(coreSettings, 'puae_retropad_options', pad_options)
    elif system.name == 'amigacdtv':
        _set(coreSettings, 'puae_retropad_options', 'disabled')
    else:
        _set(coreSettings, 'puae_retropad_options', 'jump')

    if system.name == 'amiga500' or system.name == 'amiga1200':
        # Floppy Turbo Speed
        _set_from_system(coreSettings, 'puae_floppy_speed', system, default="100")
        # 2P Gamepad Mapping (Keyrah)
        _set_from_system(coreSettings, 'puae_keyrah_keypad_mappings', system, 'keyrah_mapping', default="enabled")
        # Whdload Launcher
        _set_from_system(coreSettings, 'puae_use_whdload_prefs', system, 'whdload', default="config")
        # Disable Emulator Joystick for Pad2Key
        _set_from_system(coreSettings, 'puae_physical_keyboard_pass_through', system, 'disable_joystick', default="disabled")

    if system.name == 'amigacd32' or system.name == 'amigacdtv':
        # Boot animation first inserting CD
        _set_from_system(coreSettings, 'puae_cd_startup_delayed_insert', system, default="disabled")
        # CD Turbo Speed
        _set_from_system(coreSettings, 'puae_cd_speed', system, default="100")

    if system.name == 'amigacd32':
        # Jump on A (Blue)
        _set_from_system(coreSettings, 'puae_cd32pad_options', system, default="disabled")


def _dolphin_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Dolpin Wii

    # Wii System Languages
    _set_from_system(coreSettings, 'dolphin_language', system, 'wii_language', default='English')
    # Wii Resolution Scale
    _set_from_system(coreSettings, 'dolphin_efb_scale', system, 'wii_resolution', default="x1 (640 x 528)")
    # Anisotropic Filtering
    _set_from_system(coreSettings, 'dolphin_max_anisotropy', system, 'wii_anisotropic', default="x1")
    # Wii Tv Mode
    _set_from_system(coreSettings, 'dolphin_widescreen', system, 'wii_widescreen', default="enabled")
    # Widescreen Hack
    _set_from_system(coreSettings, 'dolphin_widescreen_hack', system, 'wii_widescreen_hack', default="disabled")
    # Shader Compilation Mode
    _set_from_system(coreSettings, 'dolphin_shader_compilation_mode', system, 'wii_shader_mode', default="sync")
    # OSD
    _set_from_system(coreSettings, 'dolphin_osd_enabled', system, 'wii_osd', default="enabled")


def _o2em_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Magnavox - Odyssey2 / Phillips Videopac+

    # Virtual keyboard transparency
    _set(coreSettings, 'o2em_vkbd_transparency', '25')
    # Emulated Hardware
    if (bios := system.get_option('o2em_bios')) is not system.MISSING:
        _set(coreSettings, 'o2em_bios', bios)
    elif system.name == 'videopacplus':
        _set(coreSettings, 'o2em_bios', 'g7400.bin')
    else:
        _set(coreSettings, 'o2em_bios', 'o2rom.bin')
    # Emulated Hardware
    if (region := system.get_option('o2em_region', 'autodetect')) != "autodetect":
        _set(coreSettings, 'o2em_region', region)
    else:
        _set(coreSettings, 'o2em_region', 'auto')
    # Swap Gamepad
    _set_from_system(coreSettings, 'o2em_swap_gamepads', system, default='disabled')
    # Crop Overscan
    _set_from_system(coreSettings, 'o2em_crop_overscan', system, default='enabled')
    # Ghosting effect
    _set_from_system(coreSettings, 'o2em_mix_frames', system, default='disabled')
    # Audio Filter
    if (low_pass_range := system.get_option('o2em_low_pass_range', '0')) != "0":
        _set(coreSettings, 'o2em_low_pass_filter', 'enabled')
        _set(coreSettings, 'o2em_low_pass_range', low_pass_range)
    else:
        _set(coreSettings, 'o2em_low_pass_filter', 'disabled')
        _set(coreSettings, 'o2em_low_pass_range',  '0')


def _mame_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # MAME/MESS/MAMEVirtual

    # Lightgun mode
    _set(coreSettings, 'mame_lightgun_mode', 'lightgun')
    # Enable cheats
    _set(coreSettings, 'mame_cheats_enable', 'enabled')
    # CPU Overclock
    _set_from_system(coreSettings, 'mame_cpu_overclock', system, default='default')
    # Video Resolution
    _set_from_system(coreSettings, 'mame_altres', system, default='640x480')
    # Disable controller profiling
    _set(coreSettings, 'mame_buttons_profiles', 'disabled')
    # Software Lists (MESS)
    _set(coreSettings, 'mame_softlists_enable', 'disabled')
    _set(coreSettings, 'mame_softlists_auto_media', 'disabled')
    # Enable config reading (for controls)
    _set(coreSettings, 'mame_read_config', 'enabled')
    # Use CLI (via CMD file) to boot
    _set(coreSettings, 'mame_boot_from_cli', 'enabled')
    # Activate mouse for Mac & Archimedes
    _set(coreSettings, 'mame_mouse_enable', 'enabled' if system.name in [ 'macintosh', 'archimedes' ] else 'disabled')


def _same_cdi_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # SAME_CDI

    # Lightgun mode
    _set(coreSettings, 'same_cdi_lightgun_mode', 'lightgun')
    # Enable cheats
    _set(coreSettings, 'same_cdi_cheats_enable', 'enabled')
    # CPU Overclock
    _set_from_system(coreSettings, 'same_cdi_cpu_overclock', system, default='default')
    # Video Resolution
    _set_from_system(coreSettings, 'same_cdi_altres', system, 'same_cdi_altres', default='640x480')
    # Disable controller profiling
    _set(coreSettings, 'same_cdi_buttons_profiles', 'disabled')
    # Software Lists (MESS)
    _set(coreSettings, 'same_cdi_softlists_enable', 'disabled')
    _set(coreSettings, 'same_cdi_softlists_auto_media', 'disabled')
    # Enable config reading (for controls)
    _set(coreSettings, 'same_cdi_read_config', 'enabled')
    # Use CLI (via CMD file) to boot
    _set(coreSettings, 'same_cdi_boot_from_cli', 'enabled')
    # Activate mouse
    _set(coreSettings, 'same_cdi_mouse_enable', 'enabled')


def _mame078plus_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # MAME 2003 Plus

    # Skip Disclaimer and Warnings
    _set(coreSettings, 'mame2003-plus_skip_disclaimer', 'enabled')
    _set(coreSettings, 'mame2003-plus_skip_warnings',   'enabled')
    # Control Mapping
    _set_from_system(coreSettings, 'mame2003-plus_analog', system, 'mame2003-plus_analog', default='digital')
    # Frameskip
    _set_from_system(coreSettings, 'mame2003-plus_frameskip', system, 'mame2003-plus_frameskip', default='0')
    # Input interface
    _set_from_system(coreSettings, 'mame2003-plus_input_interface', system, 'mame2003-plus_input_interface', default='retropad')
    # TATE Mode
    _set_from_system(coreSettings, 'mame2003-plus_tate_mode', system, 'mame2003-plus_tate_mode', default='disabled')
    # NEOGEO Bios
    _set_from_system(coreSettings, 'mame2003-plus_neogeo_bios', system, 'mame2003-plus_neogeo_bios', default='unibios33')

    # gun
    _set(coreSettings, 'mame2003-plus_xy_device', 'lightgun' if system.get_option_bool('use_guns') and guns else 'mouse')
    # gun cross
    _set_from_system(coreSettings, 'mame2003-plus_crosshair_enabled', system, 'mame2003-plus_crosshair_enabled', default='enabled' if guns_need_crosses(guns) else 'disabled')


# TODO: Add CORE options for MAME / iMame4all


def _vecx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # MB Vectrex

    # Res Multiplier
    _set_from_system(coreSettings, 'vecx_res_multi', system, 'res_multi', default='1')


def _dosbox_pure_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Microsoft DOS

    #allow to read a custom dosbox.conf present in the game directory
    coreSettings.save('dosbox_pure_conf', '"inside"')

    # CPU Type
    _set_from_system(coreSettings, 'dosbox_pure_cpu_type', system, 'pure_cpu_type', default='auto')
    # CPU Core
    if (cpu_core := system.get_option('pure_cpu_core')) != "automatic":
        _set(coreSettings, 'dosbox_pure_cpu_core', cpu_core)
    else:
        _set(coreSettings, 'dosbox_pure_cpu_core', 'auto')
    # Emulated performance (CPU Cycles)
    if (cycles := system.get_option('pure_cycles', 'automatic')) != "automatic":
        _set(coreSettings, 'dosbox_pure_cycles', cycles)
    else:
        _set(coreSettings, 'dosbox_pure_cycles', 'auto')
    # Graphics Chip type
    _set_from_system(coreSettings, 'dosbox_pure_machine', system, 'pure_machine', default='svga')
    # Memory size
    _set_from_system(coreSettings, 'dosbox_pure_memory_size', system, 'pure_memory_size', default='16')
    # Save state
    _set_from_system(coreSettings, 'dosbox_pure_savestate', system, 'pure_savestate', default='on')
    # Keyboard Layout
    _set_from_system(coreSettings, 'dosbox_pure_keyboard_layout', system, 'pure_keyboard_layout', default='us')
    # Automatic Gamepad Mapping
    _set_from_system(coreSettings, 'dosbox_pure_auto_mapping', system, 'pure_auto_mapping', default='true')
    # Joystick Analog Deadzone
    _set_from_system(coreSettings, 'dosbox_pure_joystick_analog_deadzone', system, 'pure_joystick_analog_deadzone', default='15')
    # Enable Joystick Timed Intervals
    _set_from_system(coreSettings, 'dosbox_pure_joystick_timed', system, 'pure_joystick_timed', default='true')
    # SoundBlaster Type
    _set_from_system(coreSettings, 'dosbox_pure_sblaster_type', system, 'pure_sblaster_type', default='sb16')
    # Enable Gravis Sound
    _set_from_system(coreSettings, "dosbox_pure_gus", system, 'pure_gravis', default='false')
    # Midi Type
    _set_from_system(coreSettings, 'dosbox_pure_midi', system, 'pure_midi', default='disabled')


def _bluemsx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Microsoft MSX and Colecovision

    # Auto Select Core
    if (system.name == 'colecovision'):
        _set(coreSettings, 'bluemsx_msxtype', 'ColecoVision')
    elif (system.name == 'msx1'):
        _set(coreSettings, 'bluemsx_msxtype', 'MSX')
    elif (system.name == 'msx2'):
        _set(coreSettings, 'bluemsx_msxtype', 'MSX2')
    elif (system.name == 'msx2+'):
        _set(coreSettings, 'bluemsx_msxtype', 'MSX2+')
    elif (system.name == 'msxturbor'):
        _set(coreSettings, 'bluemsx_msxtype', 'MSXturboR')
    # Forces cropping of overscanned frames
    if system.name == 'colecovision' or system.name == 'msx1':
        _set(coreSettings, 'bluemsx_overscan', 'enabled')
    else:
        _set(coreSettings, 'bluemsx_overscan', 'MSX2')
    # Reduce Sprite Flickering
    _set(coreSettings, 'bluemsx_nospritelimits', 'OFF' if system.get_option('bluemsx_nospritelimits') == "False" else 'ON')
    # Zoom, Hide Video Border
    _set_from_system(coreSettings, 'bluemsx_overscan', system, 'bluemsx_overscan', default='MSX2')


def _pce_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nec PC Engine / CD

    # Remove 16-sprites-per-scanline hardware limit
    _set_from_system(coreSettings, 'pce_nospritelimit', system, 'pce_nospritelimit', default='enabled')


def _quasi88_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nec PC-8800

    # PC Model
    _set_from_system(coreSettings, 'q88_basic_mode', system, 'q88_basic_mode', default='N88 V2')
    # CPU clock (Overclock)
    _set_from_system(coreSettings, 'q88_cpu_clock', system, 'q88_cpu_clock', default='4')
    # Use PCG-8100
    _set_from_system(coreSettings, 'q88_pcg-8100', system, 'q88_pcg-8100', default='disabled')


def _np2kai_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nec PC-9800
    # https://github.com/AZO234/NP2kai/blob/6e8f651a72c2ece37cc52e17cdaf4fdb87a6b2f9/sdl/libretro/libretro_core_options.h

    # Use the American keyboard
    _set(coreSettings, 'np2kai_keyboard', 'Us')
    # Fast memcheck at startup
    _set(coreSettings, 'np2kai_FastMC', 'ON')
    # Sound Generator: Use "fmgen" for enhanced sound rendering, not "Default"
    # _set(coreSettings, 'np2kai_usefmgen', 'fmgen')
    # PC Model
    _set_from_system(coreSettings, 'np2kai_model', system, 'np2kai_model', default='PC-9801VX')
    # CPU Feature
    _set_from_system(coreSettings, 'np2kai_cpu_feature', system, 'np2kai_cpu_feature', default='Intel 80386')
    # CPU Clock Multiplier
    _set_from_system(coreSettings, 'np2kai_clk_mult', system, 'np2kai_clk_mult', default='4')
    # RAM Size
    _set_from_system(coreSettings, 'np2kai_ExMemory', system, 'np2kai_ExMemory', default='3')
    # GDC
    _set_from_system(coreSettings, 'np2kai_gdc', system, 'np2kai_gdc', default='uPD7220')
    # Remove Scanlines (255 lines)
    if (skipline := system.get_option('np2kai_skipline', 'Full 255 lines')) != "Full 255 lines":
        _set(coreSettings, 'np2kai_skipline', 'ON' if skipline == "True" else 'OFF')
    else:
        _set(coreSettings, 'np2kai_skipline', 'Full 255 lines')
    # Real Palettes
    _set(coreSettings, 'np2kai_realpal', 'ON' if system.get_option('np2kai_realpal') == "True" else 'OFF')
    # Sound Board
    _set_from_system(coreSettings, 'np2kai_SNDboard', system, 'np2kai_SNDboard', default='PC9801-26K + 86')
    # JAST SOUND
    _set(coreSettings, 'np2kai_jast_snd', 'ON' if system.get_option('np2kai_jast_snd') == "True" else 'OFF')
    # Joypad to Keyboard Mapping
    _set_from_system(coreSettings, 'np2kai_joymode', system, 'np2kai_joymode', default='Arrows')


def _mednafen_supergrafx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nec PC Engine SuperGrafx

    # Remove 16-sprites-per-scanline hardware limit
    _set_from_system(coreSettings, 'sgx_nospritelimit', system, 'sgx_nospritelimit', default='enabled')


def _pcfx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nec PC-FX

    # Remove 16-sprites-per-scanline hardware limit
    _set_from_system(coreSettings, 'pcfx_nospritelimit', system, 'pcfx_nospritelimit', default='enabled')


def _citra_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo 3DS
    # TODO: Add CORE Options for 3DS

    # Set OpenGL rendering
    n3ds_config = RETROARCH_CONFIG / "3ds.cfg"
    if not n3ds_config.exists():
        with n3ds_config.open("w") as f:
            f.write("video_driver = \"glcore\"\n")


def _mupen64plus_next_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo 64

    # Threaded Rendering
    _set(coreSettings, 'mupen64plus-ThreadedRenderer', 'True')
    # Use High-Res Textures Pack
    # .htc files must be placed in 'Mupen64plus/cache'
    _set(coreSettings, 'mupen64plus-txHiresEnable', 'True')
    # Video 4:3 Resolution
    _set_from_system(coreSettings, 'mupen64plus-43screensize', system, 'mupen64plus-43screensize', default='320x240')
    # Video 16:9 Resolution
    _set_from_system(coreSettings, 'mupen64plus-169screensize', system, 'mupen64plus-169screensize', default='640x360')
    # Widescreen Hack
    # Increases from 4:3 to 16:9 in 3D games (bad for 2D)
    if system.get_option('mupen64plus-aspect') == '16:9 adjusted' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none":
        _set(coreSettings, 'mupen64plus-aspect', '16:9 adjusted')
    else:
        _set(coreSettings, 'mupen64plus-aspect', '4:3')
    # Bilinear Filtering
    _set(coreSettings, 'mupen64plus-BilinearMode', '3point' if system.get_option('mupen64plus-BilinearMode') == '3point' else 'standard')
    # Anti-aliasing (MSA)
    _set_from_system(coreSettings, 'mupen64plus-MultiSampling', system, 'mupen64plus-MultiSampling', default='0')
    # Texture Filtering
    _set_from_system(coreSettings, 'mupen64plus-txFilterMode', system, 'mupen64plus-txFilterMode', default='None')
    # Texture Enhancement
    _set_from_system(coreSettings, 'mupen64plus-txEnhancementMode', system, 'mupen64plus-txEnhancementMode', default='None')

    # Check if any controller packs are set to auto rumble
    auto_rumble_pak = None
    for pak in range(1, 5):
        pak_value = f'mupen64plus-pak{pak}'
        if system.get_option(pak_value) == 'auto_rumble':
            auto_rumble_pak = pak_value
            break

    if auto_rumble_pak:
        metadata = controllersConfig.getGamesMetaData(system.name, rom)
    else:
        metadata: dict[str, str] = {}

    # Controller Pak 1
    if (pak1 := system.get_option('mupen64plus-pak1')) is not system.MISSING:
        if pak1 == 'auto_rumble':
            _set(coreSettings, 'mupen64plus-pak1', 'rumble' if metadata.get("controller_rumble") == "true" else 'memory')
        else:
            _set(coreSettings, 'mupen64plus-pak1', pak1)
    else:
        _set(coreSettings, 'mupen64plus-pak1', 'memory')
    # Controller Pak 2
    if (pak2 := system.get_option('mupen64plus-pak2')) is not system.MISSING:
        if pak2 == 'auto_rumble':
            _set(coreSettings, 'mupen64plus-pak2', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'mupen64plus-pak2', pak2)
    else:
        _set(coreSettings, 'mupen64plus-pak2', 'none')
    # Controller Pak 3
    if (pak3 := system.get_option('mupen64plus-pak3')) is not system.MISSING:
        if pak3 == 'auto_rumble':
            _set(coreSettings, 'mupen64plus-pak3', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'mupen64plus-pak3', pak3)
    else:
        _set(coreSettings, 'mupen64plus-pak3', 'none')
    # Controller Pak 4
    if (pak4 := system.get_option('mupen64plus-pak4')) is not system.MISSING:
        if pak4 == 'auto_rumble':
            _set(coreSettings, 'mupen64plus-pak4', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'mupen64plus-pak4', pak4)
    else:
        _set(coreSettings, 'mupen64plus-pak4', 'none')
    # RDP Plugin
    _set_from_system(coreSettings, 'mupen64plus-rdp-plugin', system, 'mupen64plus-rdpPlugin', default='gliden64')
    # RSP Plugin
    _set_from_system(coreSettings, 'mupen64plus-rsp-plugin', system, 'mupen64plus-rspPlugin', default='hle')
    # CPU Core
    _set_from_system(coreSettings, 'mupen64plus-cpucore', system, 'mupen64plus-cpuCore', default='dynamic_recompiler')
    # Framerate
    _set_from_system(coreSettings, 'mupen64plus-Framerate', system, 'mupen64plus-Framerate', default='Original')
    # Parallel-RDP Upscaling
    _set_from_system(coreSettings, 'mupen64plus-parallel-rdp-upscaling', system, 'mupen64plus-parallel-rdp-upscaling', default='1x')
    # Joystick deadzone
    if deadzone := system.get_option('mupen64plus-deadzone'):
        _set(coreSettings, 'mupen64plus-astick-deadzone', deadzone)
    else:
        _set(coreSettings, 'mupen64plus-astick-deadzone', '0' if system.get_option_bool('use_wheels') and wheels else '15')

    # Joystick sensitivity
    _set_from_system(coreSettings, 'mupen64plus-astick-sensitivity', system, 'mupen64plus-sensitivity', default='100')


def _parallel_n64_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    _set(coreSettings, 'parallel-n64-64dd-hardware', 'disabled')
    _set(coreSettings, 'parallel-n64-boot-device',   'Default')

    # Graphics Plugin
    if gfxplugin := system.get_option('parallel-n64-gfxplugin'):
        _set(coreSettings, 'parallel-n64-gfxplugin', gfxplugin)
    else:
        # vulkan doesn't work with auto
        _set(coreSettings, 'parallel-n64-gfxplugin', 'parallel' if system.get_option('gfxbackend') == "vulkan" else 'auto')
    # Video Resolution
    _set_from_system(coreSettings, 'parallel-n64-screensize', system, 'parallel-n64-screensize', default='320x240')
    # Widescreen Hack
    # Increases from 4:3 to 16:9 in 3D games (bad for 2D)
    if system.get_option('parallel-n64-aspectratiohint') == 'widescreen' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none":
        _set(coreSettings, 'parallel-n64-aspectratiohint', 'widescreen')
    else:
        _set(coreSettings, 'parallel-n64-aspectratiohint', 'normal')
    # Texture Filtering
    _set_from_system(coreSettings, 'parallel-n64-filtering', system, 'parallel-n64-filtering', default='automatic')
    # Framerate
    _set_from_system(coreSettings, 'parallel-n64-framerate', system, 'parallel-n64-framerate', default='automatic')

    # Check if any controller packs are set to auto rumble
    auto_rumble_pak = None
    for pak in range(1, 5):
        pak_value = f'parallel-n64-pak{pak}'
        if system.get_option(pak_value) == 'auto_rumble':
            auto_rumble_pak = pak_value
            break

    if auto_rumble_pak:
        metadata = controllersConfig.getGamesMetaData(system.name, rom)
    else:
        metadata: dict[str, str] = {}

    # Controller Pak 1
    if (pak1 := system.get_option('parallel-n64-pak1')) is not system.MISSING:
        if pak1 == 'auto_rumble':
            _set(coreSettings, 'parallel-n64-pak1', 'rumble' if metadata.get("controller_rumble") == "true" else 'memory')
        else:
            _set(coreSettings, 'parallel-n64-pak1', pak1)
    else:
        _set(coreSettings, 'parallel-n64-pak1', 'memory')
    # Controller Pak 2
    if (pak2 := system.get_option('parallel-n64-pak2')) is not system.MISSING:
        if pak2 == 'auto_rumble':
            _set(coreSettings, 'parallel-n64-pak2', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'parallel-n64-pak2', pak2)
    else:
        _set(coreSettings, 'parallel-n64-pak2', 'none')
    # Controller Pak 3
    if (pak3 := system.get_option('parallel-n64-pak3')) is not system.MISSING:
        if pak3 == 'auto_rumble':
            _set(coreSettings, 'parallel-n64-pak3', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'parallel-n64-pak3', pak3)
    else:
        _set(coreSettings, 'parallel-n64-pak3', 'none')
    # Controller Pak 4
    if (pak4 := system.get_option('parallel-n64-pak4')) is not system.MISSING:
        if pak4 == 'auto_rumble':
            _set(coreSettings, 'parallel-n64-pak4', 'rumble' if metadata.get("controller_rumble") == "true" else 'none')
        else:
            _set(coreSettings, 'parallel-n64-pak4', pak4)
    else:
        _set(coreSettings, 'parallel-n64-pak4', 'none')
    # Joystick deadzone
    if deadzone := system.get_option('parallel-n64-deadzone'):
        _set(coreSettings, 'parallel-n64-astick-deadzone', deadzone)
    else:
        _set(coreSettings, 'parallel-n64-astick-deadzone', '0' if system.get_option_bool('use_wheels') and wheels else '15')

    # Joystick sensitivity
    _set_from_system(coreSettings, 'parallel-n64-astick-sensitivity', system, 'parallel-n64-sensitivity', default='100')

    # Nintendo 64-DD
    if system.name == 'n64dd':
        # 64DD Hardware
        _set(coreSettings, 'parallel-n64-64dd-hardware', 'enabled')
        # Boot device
        _set(coreSettings, 'parallel-n64-boot-device',   '64DD IPL')


def _desmume_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo DS

    # Emulate Stylus on Right Stick
    _set(coreSettings, 'desmume_pointer_device_r', 'emulated')
    # Internal Resolution
    _set_from_system(coreSettings, 'desmume_internal_resolution', system, 'internal_resolution_desmume', default='256x192')
    # Anti-aliasing (MSAA)
    _set_from_system(coreSettings, 'desmume_gfx_multisampling', system, 'multisampling', default='disabled')
    # Texture Smoothing
    _set_from_system(coreSettings, 'desmume_gfx_texture_smoothing', system, 'texture_smoothing', default='disabled')
    # Textures Upscaling (XBRZ)
    _set_from_system(coreSettings, 'desmume_gfx_texture_scaling', system, 'texture_scaling', default='1')
    # Frame Skip
    _set_from_system(coreSettings, 'desmume_frameskip', system, 'frameskip_desmume', default='0')
    # Screen Layout
    _set_from_system(coreSettings, 'desmume_screens_layout', system, 'screens_layout', default='top/bottom')


def _melonds_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Console Mode
    _set_from_system(coreSettings, 'melonds_console_mode', system, 'melonds_console_mode', default='DS')
    # Language
    _set_from_system(coreSettings, 'melonds_language', system, 'melonds_language', default='English')
    # External Firmware
    _set_from_system(coreSettings, 'melonds_use_fw_settings', system, 'melonds_use_fw_settings', default='disable')
    # Enable threaded rendering
    _set(coreSettings, 'melonds_threaded_renderer', 'enabled')
    # Emulate Stylus on Right Stick
    _set_from_system(coreSettings, 'melonds_touch_mode',  system, 'melonds_touch_mode', default='Joystick')
    # Boot game directly
    _set_from_system(coreSettings, 'melonds_boot_directly', system, 'melonds_boot_directly', default='enabled')
    # Screen Layout + Hybrid Ratio
    _set(coreSettings, 'melonds_hybrid_ratio', '2')
    if screen_layout := system.get_option('melonds_screen_layout'):
        if screen_layout   == "Hybrid Top-Ratio2":
            _set(coreSettings, 'melonds_screen_layout', 'Hybrid Top')
        elif screen_layout == "Hybrid Top-Ratio3":
            _set(coreSettings, 'melonds_screen_layout', 'Hybrid Top')
            _set(coreSettings, 'melonds_hybrid_ratio',  '3')
        elif screen_layout == "Hybrid Bottom-Ratio2":
            _set(coreSettings, 'melonds_screen_layout', 'Hybrid Bottom')
        elif screen_layout == "Hybrid Bottom-Ratio3":
            _set(coreSettings, 'melonds_screen_layout', 'Hybrid Bottom')
            _set(coreSettings, 'melonds_hybrid_ratio',  '3')
        else:
            _set(coreSettings, 'melonds_screen_layout', screen_layout)
    else:
        _set(coreSettings, 'melonds_screen_layout',     'Top/Bottom')


def _melondsds_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # System Settings
    _set_from_system(coreSettings, 'melonds_console_mode', system, 'melondsds_console_mode', default='DS')

    # Video Settings
    _set_from_system(coreSettings, 'melonds_render_mode', system, 'melondsds_render_mode', default='software')
    _set_from_system(coreSettings, 'melonds_opengl_resolution', system, 'melondsds_resolution', default='1')
    _set_from_system(coreSettings, 'melonds_opengl_better_polygons', system, 'melondsds_poygon', default='disabled')
    _set_from_system(coreSettings, 'melonds_opengl_filtering', system, 'melondsds_filtering', default='nearest')

    # Screen Settings
    _set_from_system(coreSettings, 'melonds_show_cursor', system, 'melondsds_cursor', default='nearest')
    _set_from_system(coreSettings, 'melonds_cursor_timeout', system, 'melondsds_cursor_timeout', default='3')
    _set_from_system(coreSettings, 'melonds_touch_mode', system, 'melondsds_touchmode', default='auto')
    # set 1 screen for now top/botton
    _set(coreSettings, 'melonds_number_of_screen_layouts', '1')
    _set(coreSettings, 'melonds_screen_gap', '0')
    _set(coreSettings, 'melonds_screen_layout1', 'top-bottom')

    # Firmware Settings
    _set_from_system(coreSettings, 'melonds_firmware_wfc_dns', system, 'melondsds_dns', default='178.62.43.212')
    _set_from_system(coreSettings, 'melonds_firmware_language', system, 'melondsds_language', default='default')
    _set_from_system(coreSettings, 'melonds_firmware_favorite_color', system, 'melondsds_colour', default='default')
    _set_from_system(coreSettings, 'melonds_firmware_birth_month', system, 'melondsds_month', default='default')
    _set_from_system(coreSettings, 'melonds_firmware_birth_day', system, 'melondsds_day', default='default')

    # Onscreen Display
    _set_from_system(coreSettings, 'melonds_show_unsupported_features', system, 'melondsds_show_unsupported', default='disabled')
    _set_from_system(coreSettings, 'melonds_show_bios_warnings', system, 'melondsds_show_bios', default='disabled')
    _set_from_system(coreSettings, 'melonds_show_current_layout', system, 'melondsds_show_layout', default='disabled')
    _set_from_system(coreSettings, 'melonds_show_mic_state', system, 'melondsds_show_mic', default='disabled')
    _set_from_system(coreSettings, 'melonds_show_camera_state', system, 'melondsds_show_camera', default='disabled')
    _set_from_system(coreSettings, 'melonds_show_lid_state', system, 'melondsds_show_lid', default='disabled')


def _tgbdual_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo Gameboy (Dual Screen) / GB Color (Dual Screen)

    # Emulates two Game Boy units
    _set(coreSettings, 'tgbdual_gblink_enable',    'enabled')
    # Displays the selected player screens
    _set(coreSettings, 'tgbdual_single_screen_mp', 'both players')
    # Switches the screen layout
    _set(coreSettings, 'tgbdual_screen_placement', 'left-right')
    # Switch Game Boy sound
    _set(coreSettings, 'tgbdual_audio_output',     'Game Boy #1')
    # Switches the player screens
    _set(coreSettings, 'tgbdual_switch_screens',   'normal')


def _gambatte_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo Gameboy / GB Color / GB Advance

    # GB / GBC: Use official Bootlogo
    _set_from_system(coreSettings, 'gambatte_gb_bootloader', system, 'gb_bootloader', default='enabled')
    # GB / GBC: Interframe Blending (LCD ghosting effects)
    _set_from_system(coreSettings, 'gambatte_mix_frames', system, 'gb_mix_frames', default='disabled')

    if system.name == 'gbc':
        # GBC Color Correction
        _set_from_system(coreSettings, 'gambatte_gbc_color_correction', system, 'gbc_color_correction', default='disabled')
    elif system.name == 'gb':
        _set(coreSettings, 'gambatte_gbc_color_correction', 'disabled')

    if system.name == 'gb':
        # GB: Colorization of GB games
        match system.get_option('gb_colorization'):
            case 'none':                           #No Selection --> Classic Green
                _set(coreSettings, 'gambatte_gb_colorization',     'internal')
                _set(coreSettings, 'gambatte_gb_internal_palette', 'Special 1')
            case 'GB - Disabled':                #Disabled --> Black and White Color
                _set(coreSettings, 'gambatte_gb_colorization',     'disabled')
                _set(coreSettings, 'gambatte_gb_internal_palette', 'Special 1')
            case 'GB - SmartColor':              #Smart Coloring --> Gambatte's most colorful/appropriate color
                _set(coreSettings, 'gambatte_gb_colorization',     'auto')
                _set(coreSettings, 'gambatte_gb_internal_palette', 'Special 1')
            case 'GB - Game Specific':              #Game specific --> Select automatically a game-specific Game Boy Color palette
                _set(coreSettings, 'gambatte_gb_colorization',     'GBC')
                _set(coreSettings, 'gambatte_gb_internal_palette', 'Special 1')
            case 'custom':                       #Custom Palettes --> Use the custom palettes in the bios/palettes folder
                _set(coreSettings, 'gambatte_gb_colorization',     'custom')
                _set(coreSettings, 'gambatte_gb_internal_palette', 'Special 1')
            case system.MISSING:
                _set(coreSettings, 'gambatte_gb_colorization',         'internal')      #It's an empty file, set to Classic Green
                _set(coreSettings, 'gambatte_gb_internal_palette',     'Special 1')
            case colorization:                   #User Selection
                _set(coreSettings, 'gambatte_gb_colorization',     'internal')
                _set(coreSettings, 'gambatte_gb_internal_palette', colorization)


def _mgba_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Skip BIOS intro
    _set(coreSettings, 'mgba_skip_bios', 'ON' if system.get_option('skip_bios_mgba') == "True" else 'OFF')

    # Rumble
    if system.get_option('rumble_gain') != "1":
        _set(coreSettings, 'mgba_force_gbp', 'ON')
    else:
        _set(coreSettings, 'mgba_force_gbp', 'OFF')

    if system.name != 'gba':
        # GB / GBC: Use Super Game Boy borders
        _set(coreSettings, 'mgba_sgb_borders', 'ON' if system.get_option('sgb_borders') == "True" else 'OFF')
        # GB / GBC: Color Correction
        if (color_correction := system.get_option('color_correction')) != "False":
            _set(coreSettings, 'mgba_color_correction', color_correction)
        else:
            _set(coreSettings, 'mgba_color_correction', 'OFF')

    if system.name == 'gba':
        # GBA: Solar sensor level, Boktai 1: The Sun is in Your Hand
        _set_from_system(coreSettings, 'mgba_solar_sensor_level', system, 'solar_sensor_level', default='0')
        # GBA: Frameskip
        _set_from_system(coreSettings, 'mgba_frameskip', system, 'frameskip_mgba', default='0')
    # Force Super Game Boy mode for SGB system, auto for all others
    # No current option to override - add if needed.
    if system.name == 'sgb':
        _set(coreSettings, 'mgba_gb_model', 'Super Game Boy')
        # Default border to on for SGB
        _set(coreSettings, 'mgba_sgb_borders', 'OFF' if system.get_option('sgb_borders') == "False" else 'ON')
    else:
        _set(coreSettings, 'mgba_gb_model', 'Autodetect')


def _vba_m_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # GB / GBC / GBA: Auto select fine hardware mode
    # Emulator AUTO mode not working fine
    if system.name == 'gb':
        _set(coreSettings, 'vbam_gbHardware', 'gb')
    elif system.name == 'gbc':
        _set(coreSettings, 'vbam_gbHardware', 'gbc')
    else:
        _set(coreSettings, 'vbam_gbHardware', 'gba')

    if (system.name == 'gb'):
    # GB: Colorisation of GB games
        _set_from_system(coreSettings, 'vbam_palettes', system, 'palettes', default='black and white')

    if (system.name != 'gba'):
        # GB / GBC: Use Super Game Boy borders
        if (showborders := system.get_option('showborders_gb')) and system.name == 'gb':
            _set(coreSettings, 'vbam_showborders', showborders)
            # Force SGB mode, "sgb2" is same
            _set(coreSettings, 'vbam_gbHardware', 'sgb')
        elif (showborders := system.get_option('showborders_gbc')) and system.name == 'gbc':
            _set(coreSettings, 'vbam_showborders', showborders)
            # Force SGB mode, "sgb2" is same
            _set(coreSettings, 'vbam_gbHardware', 'sgb')
        else:
            _set(coreSettings, 'vbam_showborders', 'disabled')
        # GB / GBC: Color Correction
        if (coloroption := system.get_option('gbcoloroption_gb')) and system.name == 'gb':
            _set(coreSettings, 'vbam_gbcoloroption', coloroption)
        elif (coloroption := system.get_option('gbcoloroption_gbc')) and system.name == 'gbc':
            _set(coreSettings, 'vbam_gbcoloroption', coloroption)
        else:
            _set(coreSettings, 'vbam_gbcoloroption', 'disabled')

    if (system.name == 'gba'):
        # GBA: Solar sensor level, Boktai 1: The Sun is in Your Hand
        _set_from_system(coreSettings, 'vbam_solarsensor', system, 'solarsensor', default='0')
        # GBA: Sensor Sensitivity (Gyroscope) (%)
        _set_from_system(coreSettings, 'vbam_gyro_sensitivity', system, 'gyro_sensitivity', default='10')
        # GBA: Sensor Sensitivity (Tilt) (%)
        _set_from_system(coreSettings, 'vbam_tilt_sensitivity', system, 'tilt_sensitivity', default='10')


def _nestopia_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo NES / Famicom Disk System

    # gun
    _set(coreSettings, 'nestopia_zapper_device', 'lightgun' if system.get_option_bool('use_guns') and guns else 'mouse') # Mouse mode for Zapper

    # gun cross
    _set_from_system(coreSettings, 'nestopia_show_crosshair', system, 'nestopia_show_crosshair', default='enabled' if guns_need_crosses(guns) else 'disabled')

    # Reduce Sprite Flickering
    if system.get_option('nestopia_nospritelimit') == "disabled":
        _set(coreSettings, 'nestopia_nospritelimit', 'disabled')
    else:
        _set(coreSettings, 'nestopia_nospritelimit', 'enabled')
    # Crop Overscan
    match system.get_option('nestopia_cropoverscan'):
        case "none":
            _set(coreSettings, 'nestopia_overscan_h_left', '0')
            _set(coreSettings, 'nestopia_overscan_h_right', '0')
            _set(coreSettings, 'nestopia_overscan_v_top', '0')
            _set(coreSettings, 'nestopia_overscan_v_bottom', '0')
        case "h":
            _set(coreSettings, 'nestopia_overscan_h_left', '8')
            _set(coreSettings, 'nestopia_overscan_h_right', '8')
            _set(coreSettings, 'nestopia_overscan_v_top', '0')
            _set(coreSettings, 'nestopia_overscan_v_bottom', '0')
        case "both":
            _set(coreSettings, 'nestopia_overscan_h_left', '8')
            _set(coreSettings, 'nestopia_overscan_h_right', '8')
            _set(coreSettings, 'nestopia_overscan_v_top', '8')
            _set(coreSettings, 'nestopia_overscan_v_bottom', '8')
        case _:
            _set(coreSettings, 'nestopia_overscan_h_left', '0')
            _set(coreSettings, 'nestopia_overscan_h_right', '0')
            _set(coreSettings, 'nestopia_overscan_v_top', '8')
            _set(coreSettings, 'nestopia_overscan_v_bottom', '8')
    # Palette Choice
    _set_from_system(coreSettings, 'nestopia_palette', system, 'nestopia_palette', default='consumer')
    # NTSC Filter
    _set_from_system(coreSettings, 'nestopia_blargg_ntsc_filter', system, 'nestopia_blargg_ntsc_filter', default='disabled')
    # CPU Overclock
    _set_from_system(coreSettings, 'nestopia_overclock', system, 'nestopia_overclock', default='1x')
    # 4 Player Adapter
    if (select_adapter := system.get_option('nestopia_select_adapter')) != "automatic":
        _set(coreSettings, 'nestopia_select_adapter', select_adapter)
    else:
        _set(coreSettings, 'nestopia_select_adapter', 'auto')


def _fceumm_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # gun
    _set(coreSettings, 'fceumm_zapper_mode', 'lightgun' if system.get_option_bool('use_guns') and guns else 'mouse') # FCEumm Mouse mode for Zapper

    # gun cross
    _set_from_system(coreSettings, 'fceumm_show_crosshair', system, 'fceumm_show_crosshair', default='enabled' if guns_need_crosses(guns) else 'disabled')

    # Reduce Sprite Flickering
    if system.get_option('fceumm_nospritelimit') == "disabled":
        _set(coreSettings, 'fceumm_nospritelimit', 'disabled')
    else:
        _set(coreSettings, 'fceumm_nospritelimit', 'enabled')
    # Crop Overscan
    match system.get_option('fceumm_cropoverscan'):
        case "none":
            _set(coreSettings, 'fceumm_overscan_h_left', '0')
            _set(coreSettings, 'fceumm_overscan_h_right', '0')
            _set(coreSettings, 'fceumm_overscan_v_top', '0')
            _set(coreSettings, 'fceumm_overscan_v_bottom', '0')
        case "h":
            _set(coreSettings, 'fceumm_overscan_h_left', '8')
            _set(coreSettings, 'fceumm_overscan_h_right', '8')
            _set(coreSettings, 'fceumm_overscan_v_top', '0')
            _set(coreSettings, 'fceumm_overscan_v_bottom', '0')
        case "both":
            _set(coreSettings, 'fceumm_overscan_h_left', '8')
            _set(coreSettings, 'fceumm_overscan_h_right', '8')
            _set(coreSettings, 'fceumm_overscan_v_top', '8')
            _set(coreSettings, 'fceumm_overscan_v_bottom', '8')
        case _:
            _set(coreSettings, 'fceumm_overscan_h_left', '0')
            _set(coreSettings, 'fceumm_overscan_h_right', '0')
            _set(coreSettings, 'fceumm_overscan_v_top', '8')
            _set(coreSettings, 'fceumm_overscan_v_bottom', '8')
    # Palette Choice
    _set_from_system(coreSettings, 'fceumm_palette', system, 'fceumm_palette', default='default')
    # NTSC Filter
    _set_from_system(coreSettings, 'fceumm_ntsc_filter', system, 'fceumm_ntsc_filter', default='disabled')
    # Sound Quality
    _set_from_system(coreSettings, 'fceumm_sndquality', system, 'fceumm_sndquality', default='Low')
    # PPU Overclocking
    _set_from_system(coreSettings, 'fceumm_overclocking', system, 'fceumm_overclocking', default='disabled')


def _mesen_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    _set_from_system(coreSettings, 'mesen_region', system, 'mesen_region', default='Auto')
    # Screen rotation (for homebrew)
    _set_from_system(coreSettings, 'mesen_screenrotation', system, 'mesen_screenrotation', default='None')
    # NTSC Filter
    _set_from_system(coreSettings, 'mesen_ntsc_filter', system, 'mesen_ntsc_filter', default='Disabled')
    # Sprite limit removal
    _set_from_system(coreSettings, 'mesen_nospritelimit', system, 'mesen_nospritelimit', default='disabled')
    # Palette
    _set_from_system(coreSettings, 'mesen_palette', system, 'mesen_palette', default='Default')
    # HD texture replacements
    _set_from_system(coreSettings, 'mesen_hdpacks', system, 'mesen_hdpacks', default='enabled')
    # FDS Auto-insert side A
    _set_from_system(coreSettings, 'mesen_fdsautoinsertdisk', system, 'mesen_fdsautoinsertdisk', default='disabled')
    # FDS Fast forward floppy disk loading
    _set_from_system(coreSettings, 'mesen_fdsfastforwardload', system, 'mesen_fdsfastforwardload', default='disabled')
    # RAM init state (speedrunning)
    _set_from_system(coreSettings, 'mesen_ramstate', system, 'mesen_ramstate', default='All 0s (Default)')
    # NES CPU Overclock
    _set_from_system(coreSettings, 'mesen_overclock', system, 'mesen_overclock', default='None')
    # Overclocking type (compatibility)
    _set_from_system(coreSettings, 'mesen_overclock_type', system, 'mesen_overclock_type', default='Before NMI (Recommended)')


def _pokemini_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo Pokemon Mini

    # LCD Filter
    _set_from_system(coreSettings, 'pokemini_lcdfilter', system, 'pokemini_lcdfilter', default='dotmatrix')
    # LCD Ghosting Effects
    _set_from_system(coreSettings, 'pokemini_lcdmode', system, 'pokemini_lcdmode', default='analog')


def _snes9x_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo SNES

    # Reduce sprite flickering (Hack, Unsafe)
    _set_from_system(coreSettings, 'snes9x_reduce_sprite_flicker', system, 'reduce_sprite_flicker', default='enabled')
    # Reduce Slowdown (Hack, Unsafe)
    _set_from_system(coreSettings, 'snes9x_overclock_cycles', system, 'reduce_slowdown', default='disabled')
    # SuperFX Overclocking
    _set_from_system(coreSettings, 'snes9x_overclock_superfx', system, 'overclock_superfx', default='100%')
    # Hi-Res Blending
    _set_from_system(coreSettings, 'snes9x_hires_blend', system, 'hires_blend', default='disabled')
    # Blargg NTSC Filter
    _set_from_system(coreSettings, 'snes9x_blargg', system, 'snes9x_blargg_filter', default='disabled')
    # Crosshair
    if crosshair := system.get_option('superscope_crosshair'):
        _set(coreSettings, 'snes9x_superscope_crosshair', crosshair)
        _set(coreSettings, 'snes9x_justifier1_crosshair', crosshair)
        _set(coreSettings, 'snes9x_justifier2_crosshair', crosshair)
        _set(coreSettings, 'snes9x_rifle_crosshair', crosshair)
    else:
        status = '2' if guns_need_crosses(guns) else '0'
        _set(coreSettings, 'snes9x_superscope_crosshair', status)
        _set(coreSettings, 'snes9x_justifier1_crosshair', status)
        _set(coreSettings, 'snes9x_justifier2_crosshair', status)
        _set(coreSettings, 'snes9x_rifle_crosshair', status)
    if system.get_option_bool('use_guns') and guns:
        _set(coreSettings, 'snes9x_superscope_reverse_buttons', 'disabled')


def _snes9x_next_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Reduce sprite flickering (Hack, Unsafe)
    _set_from_system(coreSettings, 'snes9x_2010_reduce_sprite_flicker', system, '2010_reduce_sprite_flicker', default='enabled')
    # Reduce Slowdown (Hack, Unsafe)
    _set_from_system(coreSettings, 'snes9x_2010_overclock_cycles', system, '2010_reduce_slowdown', default='disabled')
    # SuperFX Overclocking
    _set_from_system(coreSettings, 'snes9x_2010_overclock', system, '2010_overclock_superfx', default='10 MHz (Default)')
    # Blargg NTSC Filter
    _set_from_system(coreSettings, 'snes9x_2010_blargg', system, 'snes9x_2010_blargg_filter', default='disabled')
    # Crosshair
    _set_from_system(coreSettings, 'snes9x_2010_superscope_crosshair', system, 'superscope_crosshair', default='2' if guns_need_crosses(guns) else 'disabled')


def _bsnes_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # TODO: Add CORE options for BSnes and PocketSNES
    if system.get_option_bool('use_guns') and guns:
        _set(coreSettings, 'bsnes_touchscreen_lightgun_superscope_reverse', 'OFF')
    # Video Filters
    _set_from_system(coreSettings, 'bsnes_video_filter', system, 'bsnes_video_filter', default='disabled')


def _mesen_s_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo SNES/GB/GBC/SGB

    # Force appropriate Game Boy mode for the system (unless overriden)
    gbmodel = system.get_option('mesen-s_gbmodel')
    if gbmodel is system.MISSING:
        if system.name == 'sgb':
            _set(coreSettings, 'mesen-s_gbmodel', 'Super Game Boy')
        elif system.name == 'gb':
            _set(coreSettings, 'mesen-s_gbmodel', 'Game Boy')
        elif system.name == 'gbc':
            _set(coreSettings, 'mesen-s_gbmodel', 'Game Boy Color')
        else:
            _set(coreSettings, 'mesen-s_gbmodel', 'Auto')
    else:
        _set(coreSettings, 'mesen-s_gbmodel', gbmodel)
    # SGB2 Enable
    _set_from_system(coreSettings, 'mesen-s_sgb2', system, 'mesen-s_sgb2', default='enabled')
    # NTSC Filter
    _set_from_system(coreSettings, 'mesen-s_ntsc_filter', system, 'mesen-s_ntsc_filter', default='disabled')
    # Blending for high-res mode (Kirby's Dream Land 3 pseudo-transparency)
    _set_from_system(coreSettings, 'mesen-s_blend_high_res', system, 'mesen-s_blend_high_res', default='disabled')
    # Change sound interpolation to cubic
    _set_from_system(coreSettings, 'mesen-s_cubic_interpolation', system, 'mesen-s_cubic_interpolation', default='disabled')
    # SNES CPU Overclock
    _set_from_system(coreSettings, 'mesen-s_overclock', system, 'mesen-s_overclock', default='None')
    # Overclocking type (compatibility)
    _set_from_system(coreSettings, 'mesen-s_overclock_type', system, 'mesen-s_overclock_type', default='Before NMI')
    # SuperFX Overclock
    _set_from_system(coreSettings, 'mesen-s_superfx_overclock', system, 'mesen-s_superfx_overclock', default='100%')


def _vb_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Nintendo Virtual Boy

    # 2D Color Mode
    _set_from_system(coreSettings, 'vb_color_mode', system, '2d_color_mode', default='black & red')
    # 3D Glasses Color Mode
    _set_from_system(coreSettings, 'vb_anaglyph_preset', system, '3d_color_mode', default='disabled')


def _opera_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Panasonic 3DO

    # Audio Process on separate CPU thread
    _set(coreSettings, 'opera_dsp_threaded', 'enabled')
    # High Resolution (640x480)
    _set_from_system(coreSettings, 'opera_high_resolution', system, 'high_resolution', default='enabled')
    # CPU Overclock
    _set_from_system(coreSettings, 'opera_cpu_overclock', system, 'cpu_overclock', default='1.0x (12.50Mhz)')
    # Active Input Devices Fix
    _set_from_system(coreSettings, 'opera_active_devices', system, 'active_devices', default='1')
    # Additional game fixes
    _set(coreSettings, 'opera_hack_timing_1',    'disabled')
    _set(coreSettings, 'opera_hack_timing_3',    'disabled')
    _set(coreSettings, 'opera_hack_timing_5',    'disabled')
    _set(coreSettings, 'opera_hack_timing_6',    'disabled')
    if (fixes := system.get_option('game_fixes_opera')) != 'disabled':
        if fixes == 'timing_hack1':
            _set(coreSettings, 'opera_hack_timing_1',        'enabled')
        elif fixes == 'timing_hack3':
            _set(coreSettings, 'opera_hack_timing_3',        'enabled')
        elif fixes == 'timing_hack5':
            _set(coreSettings, 'opera_hack_timing_5',        'enabled')
        elif fixes == 'timing_hack6':
            _set(coreSettings, 'opera_hack_timing_6',        'enabled')
    # Shared nvram
    # If ROM includes the word Disc, assume it's a multi disc game, and enable shared nvram if the option isn't set.
    if storage := system.get_option('opera_nvram_storage'):
        _set(coreSettings, 'opera_nvram_storage', storage)
    elif 'disc' in str(rom).casefold():
        _set(coreSettings, 'opera_nvram_storage', 'shared')
    else:
        _set(coreSettings, 'opera_nvram_storage', 'per game')


def _xrick_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Rick Dangerous

    # Crop Borders
    if system.get_option_bool('xrick_crop_borders', True):
        _set(coreSettings, 'xrick_crop_borders', 'enabled')
    else:
        _set(coreSettings, 'xrick_crop_borders', 'disabled')
    # Cheat 1 (Trainer Mode)
    if system.get_option_bool('xrick_cheat1'):
        _set(coreSettings, 'xrick_cheat1', 'enabled')
    else:
        _set(coreSettings, 'xrick_cheat1', 'disabled')
    # Cheat 2 (Invulnerablilty Mode)
    if system.get_option_bool('xrick_cheat2'):
        _set(coreSettings, 'xrick_cheat2', 'enabled')
    else:
        _set(coreSettings, 'xrick_cheat2', 'disabled')
    # Cheat 3 (Expose Mode)
    if system.get_option_bool('xrick_cheat3'):
        _set(coreSettings, 'xrick_cheat3', 'enabled')
    else:
        _set(coreSettings, 'xrick_cheat3', 'disabled')


def _scummvm_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # ScummVM CORE Options

    # Analog Deadzone
    _set_from_system(coreSettings, 'scummvm_analog_deadzone', system, 'scummvm_analog_deadzone', default='15')
    # Gamepad Cursor Speed
    _set_from_system(coreSettings, 'scummvm_gamepad_cursor_speed', system, 'scummvm_gamepad_cursor_speed', default='1.0')
    # Speed Hack (safe)
    _set_from_system(coreSettings, 'scummvm_speed_hack', system, 'scummvm_speed_hack', default='enabled')


def _flycast_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sega Dreamcast / Atomiswave / Naomi

    # force vmu all, to save in saves (otherwise, it saves in game_dir, which is bios)
    _set(coreSettings, 'reicast_per_content_vmus',  'All VMUs')
    # Synchronous rendering
    _set_from_system(coreSettings, 'reicast_synchronous_rendering', system, 'reicast_synchronous_rendering', default='enabled')
    # DSP audio
    _set_from_system(coreSettings, 'reicast_enable_dsp', system, 'reicast_dsp', default='disabled')
    # Threaded Rendering
    _set(coreSettings, 'reicast_threaded_rendering',  'enabled')
    # Enable controller force feedback
    _set(coreSettings, 'reicast_enable_purupuru',  'enabled')
    # Crossbar Colors
    _set_from_system(coreSettings, 'reicast_lightgun1_crosshair', system, 'reicast_lightgun1_crosshair', default='Red' if guns_need_crosses(guns) else 'disabled')
    _set_from_system(coreSettings, 'reicast_lightgun2_crosshair', system, 'reicast_lightgun2_crosshair', default='Blue' if guns_need_crosses(guns) else 'disabled')
    _set_from_system(coreSettings, 'reicast_lightgun3_crosshair', system, 'reicast_lightgun3_crosshair', default='Green' if guns_need_crosses(guns) else 'disabled')
    _set_from_system(coreSettings, 'reicast_lightgun4_crosshair', system, 'reicast_lightgun4_crosshair', default='White' if guns_need_crosses(guns) else 'disabled')
    # Video resolution
    _set_from_system(coreSettings, 'reicast_internal_resolution', system, 'reicast_internal_resolution', default='640x480')
    # Textures Mip-mapping (blur)
    _set_from_system(coreSettings, 'reicast_mipmapping', system, 'reicast_mipmapping', default='disabled')
    # Anisotropic Filtering
    _set_from_system(coreSettings, 'reicast_anisotropic_filtering', system, 'reicast_anisotropic_filtering', default='off')
    # Texture Upscaling (xBRZ)
    _set_from_system(coreSettings, 'reicast_texupscale', system, 'reicast_texupscale', default='1')
    # Frame Skip
    _set_from_system(coreSettings, 'reicast_frame_skipping', system, 'reicast_frame_skipping', default='disabled')
    # Force Windows CE Mode
    _set_from_system(coreSettings, 'reicast_force_wince', system, 'reicast_force_wince', default='disabled')
    # Widescreen Cheat
    if system.get_option('reicast_widescreen_cheats') == 'enabled' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none":
        _set(coreSettings, 'reicast_widescreen_cheats', 'enabled')
    else:
        _set(coreSettings, 'reicast_widescreen_cheats', 'disabled')
    # Widescreen Hack (prefer Cheat)
    if system.get_option('reicast_widescreen_hack') == 'enabled' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none" and system.get_option('reicast_widescreen_cheats') == 'disabled':
        _set(coreSettings, 'reicast_widescreen_hack',   'enabled')
    else:
        _set(coreSettings, 'reicast_widescreen_hack',   'disabled')
    # Bios
    _set_from_system(coreSettings, 'reicast_language', system, 'reicast_language', default='Default')
    _set_from_system(coreSettings, 'reicast_region', system, 'reicast_region', default='Default')

    ## Atomiswave / Naomi

    # Screen Orientation
    if (rotation := system.get_option('screen_rotation_atomiswave')) and system.name == 'atomiswave':
        _set(coreSettings, 'reicast_screen_rotation', rotation)
    elif (rotation := system.get_option('screen_rotation_naomi')) and system.name == 'naomi':
        _set(coreSettings, 'reicast_screen_rotation', rotation)
    else:
        _set(coreSettings, 'reicast_screen_rotation', 'horizontal')

    # wheel
    _set(coreSettings, 'reicast_analog_stick_deadzone', '0%' if system.get_option_bool('use_wheels') and wheels else '15%') # default value


def _genesisplusgx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sega SG1000 / Master System / Game Gear / Megadrive / Mega CD

    # Allows each game to have its own one brm file for save without lack of space
    _set(coreSettings, 'genesis_plus_gx_bram', 'per game')
    # Sometimes needs to be forced to NTSC-U for MSU-MD to work (this is to avoid an intentionally coded lock-out screen):
    # https://arcadetv.github.io/msu-md-patches/wiki/Lockout-screen.html
    _set_from_system(coreSettings, 'genesis_plus_region_detect', system, 'gpgx_region', default='auto')
    # Reduce sprite flickering
    _set_from_system(coreSettings, 'genesis_plus_gx_no_sprite_limit', system, 'gpgx_no_sprite_limit', default='disabled')
    # Blargg NTSC filter
    if (ntsc_filter := system.get_option('gpgx_blargg_filter_md')) and system.name == 'megadrive':
        _set(coreSettings, 'genesis_plus_gx_blargg_ntsc_filter', ntsc_filter)
    elif (ntsc_filter := system.get_option('gpgx_blargg_filter_ms')) and system.name == 'mastersystem':
        _set(coreSettings, 'genesis_plus_gx_blargg_ntsc_filter', ntsc_filter)
    else:
        _set(coreSettings, 'genesis_plus_gx_blargg_ntsc_filter', 'Off')
    # Show Lightgun Crosshair
    if (cursor := system.get_option('gun_cursor_md')) and system.name == 'megadrive':
        _set(coreSettings, 'genesis_plus_gx_gun_cursor', cursor)
    elif (cursor := system.get_option('gun_cursor_ms')) and system.name == 'mastersystem':
        _set(coreSettings, 'genesis_plus_gx_gun_cursor', cursor)
    else:
        _set(coreSettings, 'genesis_plus_gx_gun_cursor', 'enabled' if guns_need_crosses(guns) else 'disabled')
    # Megadrive FM (YM2612)
    _set_from_system(coreSettings, 'genesis_plus_gx_ym2612', system, 'gpgx_fm', default='mame (ym2612)')

    # system.name == 'mastersystem'
    # Master System FM (YM2413)
    if (ym2413 := system.get_option('ym2413')) != "automatic":
        _set(coreSettings, 'genesis_plus_gx_ym2413', ym2413)
    else:
        _set(coreSettings, 'genesis_plus_gx_ym2413', 'auto')

    # system.name == 'gamegear'
    # Game Gear LCD Ghosting Filter
    _set_from_system(coreSettings, 'genesis_plus_gx_lcd_filter', system, 'lcd_filter', default='disabled')
    # Game Gear Extended Screen
    _set_from_system(coreSettings, 'genesis_plus_gx_gg_extra', system, 'gg_extra', default='disabled')

    # system.name == 'msu-md'
    # MSU-MD/MegaCD

    # Needs to be forced to sega/mega cd for MSU-MD to work.
    if cd_add_on := system.get_option('gpgx_cd_add_on'):
        _set(coreSettings, 'genesis_plus_gx_add_on', cd_add_on)
    elif system.name == 'msu-md':
        _set(coreSettings, 'genesis_plus_gx_add_on', 'sega/mega cd')
    else:
        _set(coreSettings, 'genesis_plus_gx_add_on', 'auto')

    # Volume setting is actually important, unlike MegaCD the MSU-MD is pre-amped at a different rate.
    # That is, the default level 100 will make the CD audio drown out the cartridge sound effects.
    if cdda_volume := system.get_option('gpgx_cdda_volume'):
        _set(coreSettings, 'genesis_plus_gx_cdda_volume', cdda_volume)
    elif system.name == 'msu-md':
        _set(coreSettings, 'genesis_plus_gx_cdda_volume', '70')
    else:
        _set(coreSettings, 'genesis_plus_gx_cdda_volume', '100')

    # gun
    if system.get_option_bool('use_guns') and guns:
        _set(coreSettings, 'genesis_plus_gx_gun_input', 'lightgun')


def _picodrive_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sega 32X (Sega Megadrive / MegaCD / Master System)

    # Reduce sprite flickering
    if system.get_option('picodrive_sprlim') == 'disabled':
        _set(coreSettings, 'picodrive_sprlim',   'disabled')
    else:
        _set(coreSettings, 'picodrive_sprlim',   'enabled')
    # Crop Overscan: the setting in picodrive shows overscan when enabled
    if system.get_option('picodrive_cropoverscan') == 'disabled':
        _set(coreSettings, 'picodrive_overscan', 'enabled')
    else:
        _set(coreSettings, 'picodrive_overscan', 'disabled')
    # 6 Button Controller 1
    _set_from_system(coreSettings, 'picodrive_sprlim', system, 'picodrive_controller1', default='6 button pad')
    # 6 Button Controller 2
    _set_from_system(coreSettings, 'picodrive_input2', system, 'picodrive_controller2', default='6 button pad')

    # Sega MegaCD
    # Emulate the Backup RAM Cartridge for games save (ex: Shining Force CD)
    if system.name == 'segacd':
        _set(coreSettings, 'picodrive_ramcart', 'enabled')
    else:
        _set(coreSettings, 'picodrive_ramcart', 'disabled')


def _yabasanshiro_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sega Saturn

    # Video Resolution
    _set_from_system(coreSettings, 'yabasanshiro_resolution_mode', system, 'resolution_mode', default='original')
    # Multitap
    match system.get_option('multitap_yabasanshiro'):
        case 'port1':
            _set(coreSettings, 'yabasanshiro_multitap_port1', 'enabled')
            _set(coreSettings, 'yabasanshiro_multitap_port2', 'disabled')
        case 'port2':
            _set(coreSettings, 'yabasanshiro_multitap_port1', 'disabled')
            _set(coreSettings, 'yabasanshiro_multitap_port2', 'enabled')
        case 'port12':
            _set(coreSettings, 'yabasanshiro_multitap_port1', 'enabled')
            _set(coreSettings, 'yabasanshiro_multitap_port2', 'enabled')
        case _:
            _set(coreSettings, 'yabasanshiro_multitap_port1', 'disabled')
            _set(coreSettings, 'yabasanshiro_multitap_port2', 'disabled')
    # Language
    _set_from_system(coreSettings, 'yabasanshiro_system_language', system, 'yabasanshiro_language', default='english')


def _kronos_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Set best OpenGL renderer
    _set(coreSettings, 'kronos_videocoretype', 'opengl_cs')
    # Video Resolution
    _set_from_system(coreSettings, 'kronos_resolution_mode', system, 'kronos_resolution', default='original')
    # Mesh mode
    _set_from_system(coreSettings, 'kronos_meshmode', system, 'kronos_meshmode', default='disabled')
    # Banding mode
    _set_from_system(coreSettings, 'kronos_bandingmode', system, 'kronos_bandingmode', default='disabled')
    # Share saves with Beetle
    if system.get_option('kronos_use_beetle_saves') == 'disabled':
        _set(coreSettings, 'kronos_use_beetle_saves', 'disabled')
    else:
        _set(coreSettings, 'kronos_use_beetle_saves', 'enabled')
    # Multitap
    match system.get_option('kronos_multitap'):
        case 'port1':
            _set(coreSettings, 'kronos_multitap_port1', 'enabled')
            _set(coreSettings, 'kronos_multitap_port2', 'disabled')
        case 'port2':
            _set(coreSettings, 'kronos_multitap_port1', 'disabled')
            _set(coreSettings, 'kronos_multitap_port2', 'enabled')
        case 'port12':
            _set(coreSettings, 'kronos_multitap_port1', 'enabled')
            _set(coreSettings, 'kronos_multitap_port2', 'enabled')
        case _:
            _set(coreSettings, 'kronos_multitap_port1', 'disabled')
            _set(coreSettings, 'kronos_multitap_port2', 'disabled')
    # BIOS langauge
    _set_from_system(coreSettings, 'kronos_language_id', system, 'kronos_language_id', default='English')


def _beetle_saturn_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # gun cross / wheel

    # gun
    _set_from_system(coreSettings, 'beetle_saturn_virtuagun_crosshair', system, 'beetle-saturn_crosshair', default='Cross' if guns_need_crosses(guns) else 'Off')
    # wheel
    _set(coreSettings, 'beetle_saturn_analog_stick_deadzone', '0%' if system.get_option_bool('use_wheels') and wheels else '15%')


def _px68k_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sharp X68000

    # Fresh config file
    keropi_config = BIOS / 'keropi' / 'config'
    keropi_sram = BIOS / 'keropi' / 'sram.dat'
    for f in [ keropi_config, keropi_sram ]:
        if f.exists():
            f.unlink()
    with keropi_config.open("w") as fd:
        fd.write("[WinX68k]\n")
        fd.write(f"StartDir={ROMS / 'x68000'}\n")

    # To auto launch HDD games
    _set(coreSettings, 'px68k_disk_path', 'disabled')
    # CPU Speed (Overclock)
    _set_from_system(coreSettings, 'px68k_cpuspeed', system, 'px68k_cpuspeed', default='33Mhz (OC)')
    # RAM Size
    _set_from_system(coreSettings, 'px68k_ramsize', system, 'px68k_ramsize', default='12MB')
    # Frame Skip
    _set_from_system(coreSettings, 'px68k_frameskip', system, 'px68k_frameskip', default='Full Frame')
    # Joypad Type for two players
    if joytype := system.get_option('px68k_joytype'):
        _set(coreSettings, 'px68k_joytype1', joytype)
        _set(coreSettings, 'px68k_joytype2', joytype)
    else:
        _set(coreSettings, 'px68k_joytype1', 'Default (2 Buttons)')
        _set(coreSettings, 'px68k_joytype2', 'Default (2 Buttons)')


def _81_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sinclair ZX81

    # Tape Fast Load
    _set(coreSettings, '81_fast_load', 'enabled')
    # Enables sound emulatio
    _set(coreSettings, '81_sound',     'Zon X-81')
    # Colorisation (Chroma 81)
    if chroma := system.get_option('81_chroma_81'):
        if chroma == "automatic":
            _set(coreSettings, '81_chroma_81', 'auto')
        else:
            _set(coreSettings, '81_chroma_81', chroma)
    else:
        _set(coreSettings, '81_chroma_81', 'enabled')
    # High Resolution
    if hires := system.get_option('81_highres'):
        if hires == "automatic":
            _set(coreSettings, '81_highres', 'auto')
        else:
            _set(coreSettings, '81_highres', hires)
    else:
        _set(coreSettings, '81_highres', 'WRX')


def _fuse_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sinclair ZX Spectrum

    # The most common configuration same as ZX Spectrum+
    _set_from_system(coreSettings, 'fuse_machine', system, 'fuse_machine', default='Spectrum 128K')
    # Zoom, Hide Video Border
    _set_from_system(coreSettings, 'fuse_hide_border', system, 'fuse_hide_border', default='disabled')


def _fbneo_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # SNK Neogeo AES MVS / Neogeo CD

    # Diagnostic input
    _set(coreSettings, 'fbneo-diagnostic-input', 'Start + L + R')
    # Allow RetroAchievements in hardcore mode with FBNeo
    _set(coreSettings, 'fbneo-allow-patched-romsets', 'disabled')
    # CPU Clock
    _set_from_system(coreSettings, 'fbneo-cpu-speed-adjust', system, 'fbneo-cpu-speed-adjust', default='100%')
    # Frameskip
    _set_from_system(coreSettings, 'fbneo-frameskip', system, 'fbneo-frameskip', default='0')
    # Crosshair (Lightgun)
    _set_from_system(coreSettings, 'fbneo-lightgun-crosshair-emulation', system, default='always show' if guns_need_crosses(guns) else 'always hide')
    _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-Controls", 'Light Gun' if system.get_option_bool('use_guns') and guns else 'Joystick')

    # NEOGEO
    if system.name == 'neogeo':
        # Neogeo Mode
        if mode_switch := system.get_option('fbneo-neogeo-mode-switch'):
            _set(coreSettings, "fbneo-neogeo-mode", 'DIPSWITCH')
            if mode_switch == 'MVS Asia/Europe':
                _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",  'MVS Asia/Europe ver. 5 (1 slot)')
            elif mode_switch == 'MVS USA':
                _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",  'MVS USA ver. 5 (2 slot)')
            elif mode_switch == 'MVS Japan':
                _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",  'MVS Japan ver. 5 (? slot)')
            elif mode_switch == 'AES Asia':
                _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",  'AES Asia')
            elif mode_switch == 'AES Japan':
                _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",  'AES Japan')
            else:
                _set(coreSettings, "fbneo-neogeo-mode", 'UNIBIOS')
        else:
            _set(coreSettings, "fbneo-neogeo-mode",     'UNIBIOS')
            # _set(coreSettings, f"fbneo-dipswitch-{rom.stem}-BIOS",      'Universe BIOS ver. 4.0')
        # Memory card mode
        _set_from_system(coreSettings, 'fbneo-memcard-mode', system, 'fbneo-memcard-mode', default='per-game')


def _neocd_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # SNK Neogeo CD

    # Console region
    _set_from_system(coreSettings, 'neocd_region', system, 'neocd_region', default='Japan')
    # BIOS Select
    _set_from_system(coreSettings, 'neocd_bios', system, 'neocd_bios', default='neocd_z.rom (CDZ)')
    # Per-Game saves
    if system.get_option('neocd_per_content_saves') == "False":
        _set(coreSettings, 'neocd_per_content_saves', 'Off')
    else:
        _set(coreSettings, 'neocd_per_content_saves', 'On')


def _ppsspp_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sony PSP
    _set_from_system(coreSettings, 'ppsspp_internal_resolution', system, 'ppsspp_resolution', default='480x272')


def _mednafen_psx_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Sony PSX

    # CPU Frequency Scaling (Overclock)
    _set_from_system(coreSettings, 'beetle_psx_hw_cpu_freq_scale', system, 'beetle_psx_hw_cpu_freq_scale', default='110%') # If not 110% NO options are working!
    # Show official Bootlogo
    _set_from_system(coreSettings, 'beetle_psx_hw_skip_bios', system, 'beetle_psx_hw_skip_bios', default='disabled')
    # Video Resolution
    _set_from_system(coreSettings, 'beetle_psx_hw_internal_resolution', system, 'beetle_psx_hw_internal_resolution', default='1x(native)')
    # Widescreen Hack
    if system.get_option('beetle_psx_hw_widescreen_hack') == 'enabled' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none":
        _set(coreSettings, 'beetle_psx_hw_widescreen_hack', 'enabled')
    else:
        _set(coreSettings, 'beetle_psx_hw_widescreen_hack', 'disabled')
    # Frame Duping (Speedup)
    _set_from_system(coreSettings, 'beetle_psx_hw_frame_duping', system, 'beetle_psx_hw_frame_duping', default='disabled')
    # CPU Dynarec (Speedup)
    _set_from_system(coreSettings, 'beetle_psx_hw_cpu_dynarec', system, 'beetle_psx_hw_cpu_dynarec', default='disabled')
    # Dynarec Code Invalidation
    _set_from_system(coreSettings, 'beetle_psx_hw_dynarec_invalidate', system, 'beetle_psx_hw_dynarec_invalidate', default='full')
    # Analog Stick self calibration
    _set(coreSettings, 'beetle_psx_hw_analog_calibration', 'enabled')
    # Multitap
    match system.get_option('multitap_mednafen'):
        case 'port1':
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port1', 'enabled')
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port2', 'disabled')
        case 'port2':
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port1', 'disabled')
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port2', 'enabled')
        case 'port12':
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port1', 'enabled')
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port2', 'enabled')
        case _:
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port1', 'disabled')
            _set(coreSettings, 'beetle_psx_hw_enable_multitap_port2', 'disabled')


def _duckstation_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # renderer
    if system.get_option_bool("gpu_software"):
        _set(coreSettings, 'swanstation_GPU_Renderer', 'Software')
    else:
        if gfxbackend := system.get_option("gfxbackend"):
            if gfxbackend == "vulkan":
                _set(coreSettings, 'swanstation_GPU_Renderer', 'Vulkan')
            elif gfxbackend == "gl" or gfxbackend == "glcore":
                _set(coreSettings, 'swanstation_GPU_Renderer', 'OpenGL')
            else:
                _set(coreSettings, 'swanstation_GPU_Renderer', 'Auto')
        else:
            _set(coreSettings, 'swanstation_GPU_Renderer', 'Auto')

    # Show official Bootlogo
    _set_from_system(coreSettings, 'swanstation_BIOS_PatchFastBoot', system, 'swanstation_PatchFastBoot', default='false')
    # Video Resolution
    _set_from_system(coreSettings, 'swanstation_GPU_ResolutionScale', system, 'swanstation_resolution_scale', default='1')
    # PGXP Geometry Correction
    _set_from_system(coreSettings, 'swanstation_GPU_PGXPEnable', system, 'swanstation_pgxp', default='true')
    # Anti-aliasing (MSAA/SSAA)
    _set_from_system(coreSettings, 'swanstation_GPU_MSAA', system, 'swanstation_antialiasing', default='1')
    # Texture Filtering
    _set_from_system(coreSettings, 'swanstation_GPU_TextureFilter', system, 'swanstation_texture_filtering', default='Nearest')
    # Widescreen Hack
    if system.get_option('swanstation_widescreen_hack') == 'true' and system.get_option('ratio') == "16/9" and system.get_option('bezel') == "none":
        _set(coreSettings, 'swanstation_GPU_WidescreenHack',  'true')
        _set(coreSettings, 'swanstation_Display_AspectRatio', '16:9')
    else:
        _set(coreSettings, 'swanstation_GPU_WidescreenHack',  'false')
        _set(coreSettings, 'swanstation_Display_AspectRatio', '4:3')
    # Crop Mode
    _set_from_system(coreSettings, 'swanstation_Display_CropMode', system, 'swanstation_CropMode', default='Overscan')
    # Gun crosshairs
    _set_from_system(coreSettings, 'swanstation_Controller_ShowCrosshair', system, 'swanstation_Controller_ShowCrosshair', default='true' if guns_need_crosses(guns) else '"false"')


def _pcsx2_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Fast Boot
    _set_from_system(coreSettings, 'pcsx2_fast_boot', system, 'lr_pcsx2_fast_boot', default='disabled')


def _pcsx_rearmed_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Display Games Hack Options
    _set(coreSettings, 'pcsx_rearmed_show_gpu_peops_settings', 'enabled')
    # Display Multitap/Gamepad Options
    _set(coreSettings, 'pcsx_rearmed_show_other_input_settings', 'enabled')
    # Enable Vibration
    _set(coreSettings, 'pcsx_rearmed_vibration', 'enabled')

    # Show Bios Bootlogo (Breaks some games)
    _set_from_system(coreSettings, 'pcsx_rearmed_show_bios_bootlogo', system, 'show_bios_bootlogo', default='disabled')
    # Frameskip
    _set_from_system(coreSettings, 'pcsx_rearmed_frameskip', system, 'frameskip_pcsx', default='0')
    # Enhanced resolution at the cost of lower performance
    match system.get_option('neon_enhancement'):
        case 'enabled':
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_enable',  'enabled')
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_no_main', 'disabled')
        case 'enabled_with_speedhack':
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_enable',  'enabled')
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_no_main', 'enabled')
        case _:
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_enable',  'disabled')
            _set(coreSettings, 'pcsx_rearmed_neon_enhancement_no_main', 'disabled')
    # Multitap
    _set_from_system(coreSettings, 'pcsx_rearmed_multitap', system, 'pcsx_rearmed_multitap', default='disabled')
    # Additional game fixes
    _set(coreSettings, 'pcsx_rearmed_idiablofix',                    'disabled')
    _set(coreSettings, 'pcsx_rearmed_pe2_fix',                       'disabled')
    _set(coreSettings, 'pcsx_rearmed_inuyasha_fix',                  'disabled')
    _set(coreSettings, 'pcsx_rearmed_gpu_peops_odd_even_bit',        'disabled')
    _set(coreSettings, 'pcsx_rearmed_gpu_peops_expand_screen_width', 'disabled')
    _set(coreSettings, 'pcsx_rearmed_gpu_peops_ignore_brightness',   'disabled')
    _set(coreSettings, 'pcsx_rearmed_gpu_peops_lazy_screen_update',  'disabled')
    _set(coreSettings, 'pcsx_rearmed_gpu_peops_repeated_triangles',  'disabled')
    if (fixes := system.get_option('game_fixes_pcsx')) != 'disabled':
        if fixes == 'Diablo_Music_Fix':
            _set(coreSettings, 'pcsx_rearmed_idiablofix',                    'enabled')
        elif fixes == 'Parasite_Eve':
            _set(coreSettings, 'pcsx_rearmed_pe2_fix',                       'enabled')
        elif fixes == 'InuYasha_Sengoku':
            _set(coreSettings, 'pcsx_rearmed_inuyasha_fix',                  'enabled')
        elif fixes == 'Chrono_Chross':
            _set(coreSettings, 'pcsx_rearmed_gpu_peops_odd_even_bit',        'enabled')
        elif fixes == 'Capcom_fighting':
            _set(coreSettings, 'pcsx_rearmed_gpu_peops_expand_screen_width', 'enabled')
        elif fixes == 'Lunar':
            _set(coreSettings, 'pcsx_rearmed_gpu_peops_ignore_brightness',   'enabled')
        elif fixes == 'Pandemonium':
            _set(coreSettings, 'pcsx_rearmed_gpu_peops_lazy_screen_update',  'enabled')
        elif fixes == 'Dark_Forces':
            _set(coreSettings, 'pcsx_rearmed_gpu_peops_repeated_triangles',  'enabled')
    # gun cross
    # Crossbar Colors
    for player in [ {"id": 1, "color": "red"}, {"id": 2, "color": "blue"} ]:
        _set_from_system(coreSettings, f'pcsx_rearmed_crosshair{player["id"]}', system, f'pcsx_rearmed_crosshair{player["id"]}', default=player["color"] if guns_need_crosses(guns) else 'disabled')


def _theodore_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Thomson MO5 / TO7

    # Auto run games
    _set(coreSettings, 'theodore_autorun',   'enabled')


def _potator_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # Watara SuperVision

    # Watara Color Palette
    _set_from_system(coreSettings, 'potator_palette', system, 'watara_palette', default='gameking')
    # Watara Ghosting
    _set_from_system(coreSettings, 'potator_lcd_ghosting', system, 'watara_ghosting', default='0')


## PORTs


def _prboom_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # DOOM

    # Internal resolution
    _set_from_system(coreSettings, 'prboom-resolution', system, 'prboom-resolution', default='320x200')


def _tyrquake_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # QUAKE

    # Resolution
    _set_from_system(coreSettings, 'tyrquake_resolution', system, 'tyrquake_resolution', default='640x480')
    # Frame rate
    _set_from_system(coreSettings, 'tyrquake_framerate', system, 'tyrquake_framerate', default='Auto')
    # Rumble
    _set_from_system(coreSettings, 'tyrquake_rumble', system, 'tyrquake_rumble', default='disabled')


def _mrboom_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # BOMBERMAN

    # Team mode
    _set_from_system(coreSettings, 'mrboom-aspect', system, 'mrboom-aspect', default='Native')


def _hatarib_options(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    # HatariB

    # Defaults
    _set(coreSettings, 'hatarib_statusbar', '0')
    _set(coreSettings, 'hatarib_fast_floppy', '1')
    _set(coreSettings, 'hatarib_show_welcome', '0')
    _set(coreSettings, 'hatarib_tos', '<etos1024k>')

    # Machine Type
    _set_from_system(coreSettings, 'hatarib_machine', system, 'hatarib_machine', default='0')

    # Language/Region
    _set_from_system(coreSettings, 'hatarib_region', system, 'hatarib_language', default='127')

    # CPU
    _set_from_system(coreSettings, 'hatarib_cpu', system, 'hatarib_cpu', default='-1')
    # CPU Clock
    _set_from_system(coreSettings, 'hatarib_cpu_clock', system, 'hatarib_cpu_clock', default='-1')
    # ST Memory Size
    _set_from_system(coreSettings, 'hatarib_memory', system, 'hatarib_memory', default='1024')
    # Pause Screen
    _set_from_system(coreSettings, 'hatarib_pause_osk', system, 'hatarib_pause', default='2')
    # Aspect Ratio
    _set_from_system(coreSettings, 'hatarib_aspect', system, 'hatarib_ratio', default='0')
    # Borders
    _set_from_system(coreSettings, 'hatarib_borders', system, 'hatarib_borders', default='0')

    # Harddrive image support
    rom_extension = rom.suffix.lower()
    if rom_extension == '.hd':
        _set(coreSettings, 'hatarib_hardimg', 'hatarib/hdd')
        _set(coreSettings, 'hatarib_hardboot', '1')
        _set(coreSettings, 'hatarib_hard_readonly', '1')
        match system.get_option("hatarib_drive"):
            case "ACSI":
                _set(coreSettings, 'hatarib_hardtype', '2')
            case "SCSI":
                _set(coreSettings, 'hatarib_hardtype', '3')
            case _:
                _set(coreSettings, 'hatarib_hardtype', '4')
    elif rom_extension == '.gemdos':
        _set(coreSettings, 'hatarib_hardimg', 'hatarib/hdd')
        _set(coreSettings, 'hatarib_hardboot', '1')
        _set(coreSettings, 'hatarib_hardtype', '0')
        _set(coreSettings, 'hatarib_hard_readonly', '0')
    else:
        _set(coreSettings, 'hatarib_hardimg', '')
        _set(coreSettings, 'hatarib_hardtype', '0')
        _set(coreSettings, 'hatarib_hardboot', '0')
        _set(coreSettings, 'hatarib_hard_readonly', '1')


_option_functions: dict[str, Callable[[UnixSettings, Emulator, Path, GunMapping, DeviceInfoMapping], None]] = {
    'cap32': _cap32_options,
    'atari8000': _atari8000_options,
    'virtualjaguar': _virtualjaguar_options,
    'handy': _handy_options,
    'vice_x64': _commodore_64_options,
    'vice_x64sc': _commodore_64_options,
    'vice_xscpu64': _commodore_64_options,
    'vice_x128': _commodore_128_options,
    'vice_xplus4': _commodore_plus_4_options,
    'vice_xvic': _commodore_vic_20_options,
    'vice_xpet': _commodore_pet_options,
    'puae': _commodore_amiga_options,
    'puae2021': _commodore_amiga_options,
    'dolphin': _dolphin_options,
    'o2em': _o2em_options,
    'mame': _mame_options,
    'mess': _mame_options,
    'mamevirtual': _mame_options,
    'same_cdi': _same_cdi_options,
    'mame078plus': _mame078plus_options,
    'vecx': _vecx_options,
    'dosbox_pure': _dosbox_pure_options,
    'bluemsx': _bluemsx_options,
    'pce': _pce_options,
    'pce_fast': _pce_options,
    'quasi88': _quasi88_options,
    'np2kai': _np2kai_options,
    'mednafen_supergrafx': _mednafen_supergrafx_options,
    'pcfx': _pcfx_options,
    'citra': _citra_options,
    'mupen64plus-next': _mupen64plus_next_options,
    'parallel_n64': _parallel_n64_options,
    'desmume': _desmume_options,
    'melonds': _melonds_options,
    'melondsds': _melondsds_options,
    'tgbdual': _tgbdual_options,
    'gambatte': _gambatte_options,
    'mgba': _mgba_options,
    'vba-m': _vba_m_options,
    'nestopia': _nestopia_options,
    'fceumm': _fceumm_options,
    'mesen': _mesen_options,
    'pokemini': _pokemini_options,
    'snes9x': _snes9x_options,
    'snes9x_next': _snes9x_next_options,
    'bsnes': _bsnes_options,
    'mesen-s': _mesen_s_options,
    'vb': _vb_options,
    'opera': _opera_options,
    'xrick': _xrick_options,
    'scummvm': _scummvm_options,
    'flycast': _flycast_options,
    'genesisplusgx': _genesisplusgx_options,
    'picodrive': _picodrive_options,
    'yabasanshiro': _yabasanshiro_options,
    'kronos': _kronos_options,
    'beetle-saturn': _beetle_saturn_options,
    'px68k': _px68k_options,
    '81': _81_options,
    'fuse': _fuse_options,
    'fbneo': _fbneo_options,
    'neocd': _neocd_options,
    'ppsspp': _ppsspp_options,
    'mednafen_psx': _mednafen_psx_options,
    'swanstation': _duckstation_options,
    'duckstation': _duckstation_options,
    'pcsx2': _pcsx2_options,
    'pcsx_rearmed': _pcsx_rearmed_options,
    'theodore': _theodore_options,
    'potator': _potator_options,
    'prboom': _prboom_options,
    'tyrquake': _tyrquake_options,
    'mrboom': _mrboom_options,
    'hatarib': _hatarib_options,
}


def generateCoreSettings(
    coreSettings: UnixSettings, system: Emulator, rom: Path, guns: GunMapping, wheels: DeviceInfoMapping, /,
) -> None:
    set_options = _option_functions.get(system.core)
    if set_options is not None:
        set_options(coreSettings, system, rom, guns, wheels)

    # Custom : Allow the user to configure directly retroarchcore.cfg via batocera.conf via lines like : snes.retroarchcore.opt=val
    for user_config, value in system.option_items(starts_with="retroarchcore."):
        _set(coreSettings, user_config, value)

def generateHatariConf(hatariConf: Path) -> None:
    hatariConfig = CaseSensitiveConfigParser(interpolation=None)
    if hatariConf.exists():
        hatariConfig.read(hatariConf)

    # update the configuration file
    with ensure_parents_and_open(hatariConf, 'w') as configfile:
        hatariConfig.write(configfile)
