from __future__ import annotations

from os import environ
from pathlib import Path
from typing import TYPE_CHECKING

from ... import Command
from ...batoceraPaths import BIOS, CONFIGS, ensure_parents_and_open
from ...controller import generate_sdl_game_controller_config, write_sdl_controller_db
from ...utils.configparser import CaseSensitiveConfigParser
from ..Generator import Generator

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from ...types import HotkeysContext


class DuckstationGenerator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "duckstation",
            "keys": { "exit": ["KEY_LEFTALT", "KEY_F4"], "menu": "KEY_F7",
                      "restore_state": "KEY_F1", "save_state": "KEY_F2", "previous_slot": "KEY_F3", "next_slot": "KEY_F4" }
    }

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        # Test if it's a m3u file
        if rom.suffix == ".m3u":
            rom = rewriteM3uFullPath(rom)

        if Path('/usr/bin/duckstation-qt').exists():
            commandArray = ["duckstation-qt", "-batch", "-nogui", "--", rom ]
        else:
            commandArray = ["duckstation-nogui", "-batch", "-fullscreen", "--", rom ]

        settings = CaseSensitiveConfigParser(interpolation=None)
        settings_path = CONFIGS / "duckstation" / "settings.ini"
        if settings_path.exists():
            settings.read(settings_path)

        ## [Main]
        if not settings.has_section("Main"):
            settings.add_section("Main")
        # Settings, Language and ConfirmPowerOff
        settings.set("Main", "SettingsVersion", "3") # Probably to be updated in the future
        settings.set("Main", "InhibitScreensaver", "true")
        settings.set("Main", "StartPaused", "false")
        # Force Fullscreen
        settings.set("Main", "StartFullscreen", "true")
        settings.set("Main", "PauseOnFocusLoss", "false")
        settings.set("Main", "PauseOnMenu", "true")
        settings.set("Main", "ConfirmPowerOff", "false")
        # Force applying game Settings fixes
        settings.set("Main","ApplyGameSettings", "true")
        # Remove wizard
        settings.set("Main","SetupWizardIncomplete", "false")
        # overclock
        settings.set("Main","EmulationSpeed", system.get_option_str("duckstation_clocking", "1"))
        # host refresh rate
        settings.set("Main","SyncToHostRefreshRate", system.get_option_str("duckstation_hrr", "false"))

        # Rewind
        #if system.isOptSet('rewind') and system.getOptBoolean('rewind'):
        settings.set("Main","RewindEnable",    "true")
        settings.set("Main","RewindFrequency", "1")        # Frame skipped each seconds
        match system.get_option_str("duckstation_rewind"):
            case '120' | '90' | '60' | '30' | '15' as rewind:
                settings.set("Main","RewindSaveSlots", rewind)  # Total duration available in sec
            case '10':
                settings.set("Main","RewindSaveSlots", "100")
                settings.set("Main","RewindFrequency", "0.100000")
            case '5':
                settings.set("Main","RewindSaveSlots", "50")
                settings.set("Main","RewindFrequency", "0.050000")
            case _:
                settings.set("Main","RewindEnable", "false")
        # Discord
        settings.set("Main","EnableDiscordPresence", "false")
        # Language
        settings.set("Main", "Language", getLangFromEnvironment())

        ## [ControllerPorts]
        if not settings.has_section("ControllerPorts"):
            settings.add_section("ControllerPorts")
        settings.set("ControllerPorts", "ControllerSettingsMigrated", "true")
        settings.set("ControllerPorts", "MultitapMode", "Disabled")
        settings.set("ControllerPorts", "PointerXScale", "8")
        settings.set("ControllerPorts", "PointerYScale", "8")
        settings.set("ControllerPorts", "PointerXInvert", "false")
        settings.set("ControllerPorts", "PointerYInvert", "false")

        ## [Console]
        if not settings.has_section("Console"):
            settings.add_section("Console")
        # Region
        settings.set("Console", "Region", system.get_option_str("duckstation_region", "Auto"))
        # Enable Cheats
        settings.set("Console", "EnableCheats", system.get_option_str("duckstation_cheats", "false"))

        ## [BIOS]
        if not settings.has_section("BIOS"):
            settings.add_section("BIOS")
        settings.set("BIOS", "SearchDirectory", "/userdata/bios")
        # Boot Logo
        settings.set("BIOS", "PatchFastBoot", system.get_option_str("duckstation_PatchFastBoot", "false"))
        # Find & populate BIOS
        found_bios = find_bios(bios_lists)

        if not found_bios:
            raise Exception("No PSX1 BIOS found")

        # Set BIOS paths
        if "Uni" in found_bios:
            uni_bios = found_bios["Uni"]
            settings.set("BIOS", "PathNTSCU", uni_bios)
            settings.set("BIOS", "PathPAL", uni_bios)
            settings.set("BIOS", "PathNTSCJ", uni_bios)
        else:
            region_mapping = {"NTSCU": "PathNTSCU", "PAL": "PathPAL", "NTSCJ": "PathNTSCJ"}
            for region, bios in found_bios.items():
                settings.set("BIOS", region_mapping[region], bios)

        ## [CPU]
        if not settings.has_section("CPU"):
            settings.add_section("CPU")
        # ExecutionMode
        settings.set("CPU", "ExecutionMode", system.get_option_str("duckstation_executionmode", "Recompiler"))

        ## [GPU]
        if not settings.has_section("GPU"):
            settings.add_section("GPU")
        # Renderer
        settings.set("GPU", "Renderer", system.get_option_str("duckstation_gfxbackend", "OpenGL"))
        # Multisampling force (MSAA or SSAA) - no GUI option anymore...
        settings.set("GPU", "PerSampleShading", "false")
        settings.set("GPU", "Multisamples", "1")
        # Threaded Presentation (Vulkan Improve)
        settings.set("GPU", "ThreadedPresentation", system.get_option_str("duckstation_threadedpresentation", "false"))
        # Internal resolution
        settings.set("GPU", "ResolutionScale", system.get_option_str("duckstation_resolution_scale", "1"))
        # WideScreen Hack
        settings.set("GPU", "WidescreenHack", system.get_option_str("duckstation_widescreen_hack", "false"))
        # Force 60hz
        settings.set("GPU", "ForceNTSCTimings", system.get_option_str("duckstation_60hz", "false"))
        # TextureFiltering
        settings.set("GPU", "TextureFilter", system.get_option_str("duckstation_texture_filtering", "Nearest"))
        # PGXP - enabled by default
        if pgxp := system.get_option_str("duckstation_pgxp"):
            settings.set("GPU", "PGXPEnable", pgxp)
            settings.set("GPU", "PGXPCulling", pgxp)
            settings.set("GPU", "PGXPTextureCorrection", pgxp)
            settings.set("GPU", "PGXPPreserveProjFP", pgxp)
        else:
            settings.set("GPU", "PGXPEnable", "true")
            settings.set("GPU", "PGXPCulling", "true")
            settings.set("GPU", "PGXPTextureCorrection", "true")
            settings.set("GPU", "PGXPPreserveProjFP", "true")
        # True Color
        settings.set("GPU", "TrueColor", system.get_option_str("duckstation_truecolour", "false"))
        # Scaled Dithering
        settings.set("GPU", "ScaledDithering", system.get_option_str("duckstation_dithering", "true"))
        # Disable Interlacing
        settings.set("GPU", "DisableInterlacing", system.get_option_str("duckstation_interlacing", "false"))
        # Anti-Aliasing
        if (antialiasing := system.get_option_str("duckstation_antialiasing")) is not system.MISSING:
            if 'ssaa' in antialiasing:
                settings.set("GPU", "PerSampleShading", "true")
                settings.set("GPU", "Multisamples", antialiasing.split('-')[0])
            else:
                settings.set("GPU", "Multisamples", antialiasing)
                settings.set("GPU", "PerSampleShading", "false")

        ## [Display]
        if not settings.has_section("Display"):
            settings.add_section("Display")
        # Aspect Ratio
        if (ratio := system.get_option_str("duckstation_ratio")) is not system.MISSING:
            settings.set("Display", "AspectRatio", ratio)
            if ratio != "4:3":
                system.config['bezel'] = "none"
        else:
            settings.set("Display", "AspectRatio", "Auto (Game Native)")
        # Vsync
        settings.set("Display", "VSync", system.get_option_str("duckstation_vsync", "false"))
        # CropMode
        settings.set("Display", "CropMode", system.get_option_str("duckstation_CropMode", "Overscan"))
        # Enable Frameskipping = option missing
        settings.set("Display", "DisplayAllFrames", "false")
        # OSD Messages
        settings.set("Display", "ShowOSDMessages", system.get_option_str("duckstation_osd", "false"))
        # Optimal frame pacing
        settings.set("Display","DisplayAllFrames", system.get_option_str("duckstation_ofp", "false"))
        # Integer Scaling
        settings.set("Display","IntegerScaling", system.get_option_str("duckstation_integer", "false"))
        # Linear Filtering
        settings.set("Display","LinearFiltering", system.get_option_str("duckstation_linear", "false"))
        # Stretch
        if (stretch := system.get_option_str("duckstation_stretch")) is not system.MISSING and stretch == "true":
            settings.set("Display","Stretch", stretch)
            if system.get_option_str("duckstation_integer", "false") == "false":
                system.config['bezel'] = "none"
        else:
            settings.set("Display","Stretch", "false")

        ## [Audio]
        if not settings.has_section("Audio"):
            settings.add_section("Audio")
        settings.set("Audio","StretchMode", system.get_option_str("duckstation_audio_mode", "TimeStretch"))

        ## [GameList]
        if not settings.has_section("GameList"):
            settings.add_section("GameList")
        settings.set("GameList" , "RecursivePaths", "/userdata/roms/psx")

        ## [Cheevos]
        if not settings.has_section("Cheevos"):
            settings.add_section("Cheevos")
        # RetroAchievements
        if system.get_option_bool('retroachievements'):
            headers   = {"Content-type": "text/plain", "User-Agent": "Batocera.linux"}  # noqa: F841
            login_url = "https://retroachievements.org/"  # noqa: F841
            username  = system.get_option_str('retroachievements.username', "")
            password  = system.get_option_str('retroachievements.password', "")  # noqa: F841
            hardcore  = system.get_option_str('retroachievements.hardcore', "")
            presence  = system.get_option_str('retroachievements.richpresence', "")
            indicator = system.get_option_str('retroachievements.challenge_indicators', "")
            leaderbd  = system.get_option_str('retroachievements.leaderboards', "")
            token     = system.get_option_str('retroachievements.token', "")
            settings.set("Cheevos", "Enabled",       "true")
            settings.set("Cheevos", "Username",      username)
            settings.set("Cheevos", "Token",         token)
            if hardcore == '1':
                settings.set("Cheevos", "ChallengeMode", "true")    # For "hardcore" retroachievement points (no save, no rewind...)
            else:
                settings.set("Cheevos", "ChallengeMode", "false")
            if presence == '1':
                settings.set("Cheevos", "RichPresence",  "true")    # Enable rich presence information will be collected and sent to the server where supported
            else:
                settings.set("Cheevos", "RichPresence",  "false")
            if indicator == '1':
                settings.set("Cheevos", "PrimedIndicators",  "true")
            else:
                settings.set("Cheevos", "PrimedIndicators",  "false")
            if leaderbd == '1':
                settings.set("Cheevos", "Leaderboards",  "true")
            else:
                settings.set("Cheevos", "Leaderboards",  "false")
            #settings.set("Cheevos", "UseFirstDiscFromPlaylist", "false") # When enabled, the first disc in a playlist will be used for achievements, regardless of which disc is active
            #settings.set("Cheevos", "TestMode",      "false")            # DuckStation will assume all achievements are locked and not send any unlock notifications to the server.
        else:
            settings.set("Cheevos", "Enabled", "false")

        ## [TextureReplacements]
        if not settings.has_section("TextureReplacements"):
            settings.add_section("TextureReplacements")
        # Texture Replacement saves\textures\psx game id - by default in Normal
        match system.get_option_str("duckstation_custom_textures"):
            case '0':
                settings.set("TextureReplacements", "EnableVRAMWriteReplacements", "false")
                settings.set("TextureReplacements", "PreloadTextures",  "false")
            case 'preload':
                settings.set("TextureReplacements", "EnableVRAMWriteReplacements", "true")
                settings.set("TextureReplacements", "PreloadTextures",  "true")
            case _:
                settings.set("TextureReplacements", "EnableVRAMWriteReplacements", "true")
                settings.set("TextureReplacements", "PreloadTextures",  "false")

        if not settings.has_section("InputSources"):
            settings.add_section("InputSources")
        settings.set("InputSources", "SDL", "true")
        settings.set("InputSources", "SDLControllerEnhancedMode", "false")
        settings.set("InputSources", "Evdev", "false")
        settings.set("InputSources", "XInput", "false")
        settings.set("InputSources", "RawInput", "false")

        ## [MemoryCards]
        if not settings.has_section("MemoryCards"):
            settings.add_section("MemoryCards")
        # Set memory card location
        settings.set("MemoryCards", "Directory", "../../../saves/duckstation/memcards")

        ## [Folders]
        if not settings.has_section("Folders"):
            settings.add_section("Folders")
        # Set other folder locations too
        settings.set("Folders", "Cache", "../../cache/duckstation")
        settings.set("Folders", "Screenshots", "../../../screenshots")
        settings.set("Folders", "SaveStates", "../../../saves/duckstation")
        settings.set("Folders", "Cheats", "../../../cheats/duckstation")

        ## [Pad]
        # Clear existing Pad(x) configs
        for i in range(1, 9):
            if settings.has_section("Pad" + str(i)):
                settings.remove_section("Pad" + str(i))
        # Now create Pad1 - 8 None to start
        for i in range(1, 9):
            settings.add_section("Pad" + str(i))
            settings.set("Pad" + str(i), "Type", "None")
        # Start with mutitap disabled
        settings.set("ControllerPorts", "MultitapMode", "Disabled")
        # Now add the controller config based on the ES type & number connected
        for nplayer, pad in enumerate(sorted(playersControllers.values())[0:8], start=1):
            # automatically add the multi-tap
            if nplayer > 2:
                settings.set("ControllerPorts", "MultitapMode", "Port1Only")
                if nplayer > 4:
                    settings.set("ControllerPorts", "MultitapMode", "BothPorts")
            pad_num = f"Pad{nplayer}"
            gun_num = f"Pointer-{pad.index}"
            sdl_num = f"SDL-{pad.index}"
            ctrl_num = "Controller" + str(nplayer)
            # SDL2 configs are always the same for controllers
            settings.set(pad_num, "Type", system.get_option_str("duckstation_" + ctrl_num, "DigitalController"))
            settings.set(pad_num, "Up", sdl_num+"/DPadUp")
            settings.set(pad_num, "Right", sdl_num+"/DPadRight")
            settings.set(pad_num, "Down", sdl_num+"/DPadDown")
            settings.set(pad_num, "Left", sdl_num+"/DPadLeft")
            settings.set(pad_num, "Triangle", sdl_num+"/Y")
            settings.set(pad_num, "Circle", sdl_num+"/B")
            settings.set(pad_num, "Cross", sdl_num+"/A")
            settings.set(pad_num, "Square", sdl_num+"/X")
            settings.set(pad_num, "Select", sdl_num+"/Back")
            settings.set(pad_num, "Start", sdl_num+"/Start")
            settings.set(pad_num, "L1", sdl_num+"/LeftShoulder")
            settings.set(pad_num, "R1", sdl_num+"/RightShoulder")
            settings.set(pad_num, "L2", sdl_num+"/+LeftTrigger")
            settings.set(pad_num, "R2", sdl_num+"/+RightTrigger")
            settings.set(pad_num, "L3", sdl_num+"/LeftStick")
            settings.set(pad_num, "R3", sdl_num+"/RightStick")
            settings.set(pad_num, "LLeft", sdl_num+"/-LeftX")
            settings.set(pad_num, "LRight", sdl_num+"/+LeftX")
            settings.set(pad_num, "LDown", sdl_num+"/+LeftY")
            settings.set(pad_num, "LUp", sdl_num+"/-LeftY")
            settings.set(pad_num, "RLeft", sdl_num+"/-RightX")
            settings.set(pad_num, "RRight", sdl_num+"/+RightX")
            settings.set(pad_num, "RDown", sdl_num+"/+RightY")
            settings.set(pad_num, "RUp", sdl_num+"/-RightY")
            settings.set(pad_num, "SmallMotor", sdl_num+"/SmallMotor")
            settings.set(pad_num, "LargeMotor", sdl_num+"/LargeMotor")
            settings.set(pad_num, "VibrationBias", "8")
            # D-Pad to Joystick
            if (digitalmode := system.get_option_str("duckstation_digitalmode")) is not system.MISSING:
                settings.set(pad_num, "AnalogDPadInDigitalMode", digitalmode)
                if system.get_option_str("duckstation_" + ctrl_num) == "AnalogController":
                    settings.set(pad_num, "Analog", sdl_num+"/Guide")
            else:
                settings.set(pad_num, "AnalogDPadInDigitalMode", "false")
            # NeGcon ?
            if system.get_option_str("duckstation_" + ctrl_num) == "NeGcon":
                settings.set(pad_num, "A", sdl_num+"/B")
                settings.set(pad_num, "B", sdl_num+"/Y")
                settings.set(pad_num, "I", sdl_num+"/+RightTrigger")
                settings.set(pad_num, "II", sdl_num+"/+LeftTrigger")
                settings.set(pad_num, "L", sdl_num+"/LeftShoulder")
                settings.set(pad_num, "R", sdl_num+"/RightShoulder")
                settings.set(pad_num, "SteeringLeft", sdl_num+"/-LeftX")
                settings.set(pad_num, "SteeringRight", sdl_num+"/+LeftX")
            # Guns
            if system.get_option_bool("use_guns") and guns:
                # Justifier compatible ROM...
                if "gun_type" in metadata and metadata["gun_type"] == "justifier":
                    settings.set(pad_num, "Type", "Justifier")
                    settings.set(pad_num, "Trigger", gun_num+"/LeftButton")
                    settings.set(pad_num, "Start", gun_num+"/RightButton")
                # Default or GunCon compatible ROM...
                else:
                    settings.set(pad_num, "Type", "GunCon")
                    settings.set(pad_num, "Trigger", gun_num+"/LeftButton")

                ### find a keyboard key to simulate the action of the player (always like button 2) ; search in batocera.conf, else default config
                pedalsKeys = {1: "c", 2: "v", 3: "b", 4: "n"}
                pedalkey = None
                pedalcname = f"controllers.pedals{nplayer}"
                if (config_pedalkey := system.get_option_str(pedalcname)) is not system.MISSING:
                    pedalkey = config_pedalkey
                else:
                    if nplayer in pedalsKeys:
                        pedalkey = pedalsKeys[nplayer]
                if pedalkey is None:
                    settings.set(pad_num, "A", gun_num+"/RightButton")
                else:
                    settings.set(pad_num, "A", gun_num+"/RightButton & Keyboard/"+pedalkey.upper())
                ###
                settings.set(pad_num, "B", gun_num+"/MiddleButton")
                if system.get_option_str("duckstation_" + ctrl_num) == "GunCon":
                    settings.set(pad_num, "Trigger", sdl_num+"/+RightTrigger")
                    settings.set(pad_num, "ShootOffscreen", sdl_num+"/+LeftTrigger")
                    settings.set(pad_num, "A", sdl_num+"/A")
                    settings.set(pad_num, "B", sdl_num+"/B")
            # Guns crosshair
            settings.set(pad_num, "CrosshairScale", system.get_option_str("duckstation_crosshair", "0"))
            # Mouse
            if system.get_option_str("duckstation_" + ctrl_num) == "PlayStationMouse":
                settings.set(pad_num, "Right", sdl_num+"/B")
                settings.set(pad_num, "Left", sdl_num+"/A")
                settings.set(pad_num, "RelativeMouseMode", sdl_num+"true")

        ## [Hotkeys]
        if not settings.has_section("Hotkeys"):
            settings.add_section("Hotkeys")
        # Force defaults to be aligned with evmapy
        settings.set("Hotkeys", "FastForward",                 "Keyboard/Tab")
        settings.set("Hotkeys", "Reset",                       "Keyboard/F6")
        settings.set("Hotkeys", "LoadSelectedSaveState",       "Keyboard/F1")
        settings.set("Hotkeys", "SaveSelectedSaveState",       "Keyboard/F2")
        settings.set("Hotkeys", "SelectPreviousSaveStateSlot", "Keyboard/F3")
        settings.set("Hotkeys", "SelectNextSaveStateSlot",     "Keyboard/F4")
        settings.set("Hotkeys", "Screenshot",                  "Keyboard/F10")
        settings.set("Hotkeys", "Rewind",                      "Keyboard/F5")
        settings.set("Hotkeys", "OpenPauseMenu",               "Keyboard/F7")
        settings.set("Hotkeys", "ChangeDisc",                  "Keyboard/F8")
        if settings.has_option('Hotkeys', 'OpenQuickMenu'):
            settings.remove_option('Hotkeys', 'OpenQuickMenu')

        ## [CDROM]
        if not settings.has_section("CDROM"):
            settings.add_section("CDROM")
        settings.set("CDROM", "AllowBootingWithoutSBIFile", system.get_option_str("duckstation_boot_without_sbi", "false"))

        ## [UI]
        if not settings.has_section("UI"):
            settings.add_section("UI")
        settings.set("UI", "UnofficialBuildWarningConfirmed", "true")

        # Save config
        with ensure_parents_and_open(settings_path, 'w') as configfile:
            settings.write(configfile)

        # write our own gamecontrollerdb.txt file before launching the game
        dbfile = "/usr/share/duckstation/resources/gamecontrollerdb.txt"
        write_sdl_controller_db(playersControllers, dbfile)

        # check if we're running wayland
        qt_qpa_platform = "wayland" if environ.get("WAYLAND_DISPLAY") else "xcb"

        # use their modified shaderc library
        return Command.Command(
            array=commandArray,
            env={
                "LD_LIBRARY_PATH": "/usr/stenzek-shaderc/lib:/usr/lib",
                "XDG_CONFIG_HOME": CONFIGS,
                "QT_QPA_PLATFORM": qt_qpa_platform,
                "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers),
                "SDL_JOYSTICK_HIDAPI": "0"
            }
        )

def getLangFromEnvironment():
    lang = environ['LANG'][:5]
    availableLanguages = { "en_US": "en",
                           "de_DE": "de",
                           "fr_FR": "fr",
                           "es_ES": "es",
                           "he_IL": "he",
                           "it_IT": "it",
                           "ja_JP": "ja",
                           "nl_NL": "nl",
                           "pl_PL": "pl",
                           "pt_BR": "pt-br",
                           "pt_PT": "pt-pt",
                           "ru_RU": "ru",
                           "zh_CN": "zh-cn"
    }
    if lang in availableLanguages:
        return availableLanguages[lang]
    return availableLanguages["en_US"]

def rewriteM3uFullPath(m3u: Path) -> Path:
    # Rewrite a clean m3u file with valid fullpath

    # get initialm3u
    with m3u.open() as f:
        firstline = f.readline().rstrip()  # Get first line in m3u

    initialfirstdisc = Path("/tmp") / Path(firstline).with_suffix(".m3u").name  # Generating a temp path with the first iso filename in m3u

    # create a temp m3u to bypass Duckstation m3u bad pathfile
    fulldirname = m3u.parent
    with initialfirstdisc.open("w"):
        pass

    with m3u.open() as initialm3u, initialfirstdisc.open('a') as f1:
        for line in initialm3u:
            # handle both "/MGScd1.chd" and "MGScd1.chd"
            newpath = fulldirname / (line[1:] if line[0] == "/" else line)
            f1.write(str(newpath))

    return initialfirstdisc  # Return the tempm3u pathfile written with valid fullpath

def find_bios(bios_lists: Mapping[str, Sequence[str]]):
    found_bios: dict[str, str] = {}

    try:
        files_lower = {f.name.lower(): f.name for f in BIOS.iterdir()}
    except OSError as e:
        raise Exception(f"Unable to read BIOS directory: {BIOS}") from e

    for region, bios_list in bios_lists.items():
        for bios in bios_list:
            if bios.lower() in files_lower:
                found_bios[region] = files_lower[bios.lower()]
                break

    return found_bios

# Define BIOS lists
bios_lists = {
    "NTSCU": ["scph101.bin", "scph1001.bin", "scph5501.bin", "scph7001.bin", "scph7501.bin"],
    "PAL": ["scph1002.bin", "scph5502.bin", "scph5552.bin", "scph7002.bin", "scph7502.bin", "scph9002.bin", "scph102a.bin", "scph102b.bin"],
    "NTSCJ": ["scph100.bin", "scph1000.bin", "scph3000.bin", "scph3500.bin", "scph5500.bin", "scph7000.bin", "scph7003.bin"],
    "Uni": ["psxonpsp660.bin", "ps1_rom.bin"]
}
