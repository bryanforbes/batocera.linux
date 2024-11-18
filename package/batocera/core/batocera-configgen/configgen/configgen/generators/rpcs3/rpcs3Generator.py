from __future__ import annotations

import logging
import re
import shutil
from typing import TYPE_CHECKING, Any, cast

from ruamel.yaml import YAML

from ... import Command
from ...batoceraPaths import BIOS, CACHE, CONFIGS, mkdir_if_not_exists
from ...controller import generate_sdl_game_controller_config, write_sdl_controller_db
from ...utils import vulkan
from ...utils.configparser import CaseSensitiveConfigParser
from ..Generator import Generator
from . import rpcs3Controllers
from .rpcs3Paths import RPCS3_BIN, RPCS3_CONFIG, RPCS3_CONFIG_DIR, RPCS3_CURRENT_CONFIG

if TYPE_CHECKING:
    from ...types import HotkeysContext, Resolution

_logger = logging.getLogger(__name__)

class Rpcs3Generator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "rpcs3",
            "keys": { "exit": ["KEY_LEFTALT", "KEY_F4"] }
        }

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):

        rpcs3Controllers.generateControllerConfig(system, playersControllers)

        # Taking care of the CurrentSettings.ini file
        mkdir_if_not_exists(RPCS3_CURRENT_CONFIG.parent)

        # Generates CurrentSettings.ini with values to disable prompts on first run

        rpcsCurrentSettings = CaseSensitiveConfigParser(interpolation=None)
        if RPCS3_CURRENT_CONFIG.exists():
            rpcsCurrentSettings.read(RPCS3_CURRENT_CONFIG)

        # Sets Gui Settings to close completely and disables some popups
        if not rpcsCurrentSettings.has_section("main_window"):
            rpcsCurrentSettings.add_section("main_window")

        rpcsCurrentSettings.set("main_window", "confirmationBoxExitGame", "false")
        rpcsCurrentSettings.set("main_window", "infoBoxEnabledInstallPUP","false")
        rpcsCurrentSettings.set("main_window", "infoBoxEnabledWelcome","false")

        with RPCS3_CURRENT_CONFIG.open("w") as configfile:
            rpcsCurrentSettings.write(configfile)

        mkdir_if_not_exists(RPCS3_CONFIG.parent)

        # Generate a default config if it doesn't exist otherwise just open the existing
        rpcs3ymlconfig: dict[str, dict[str, Any]] = {}
        if RPCS3_CONFIG.is_file():
            with RPCS3_CONFIG.open("r") as stream:
                yaml = YAML(typ='safe', pure=True)
                rpcs3ymlconfig = cast(dict[str, dict[str, Any]], yaml.load(stream) or {})

        # Add Nodes if not in the file
        if "Core" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Core"] = {}
        if "VFS" not in rpcs3ymlconfig:
            rpcs3ymlconfig["VFS"] = {}
        if "Video" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Video"] = {}
        if "Audio" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Audio"] = {}
        if "Input/Output" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Input/Output"] = {}
        if "System" not in rpcs3ymlconfig:
            rpcs3ymlconfig["System"] = {}
        if "Net" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Net"] = {}
        if "Savestate" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Savestate"] = {}
        if "Miscellaneous" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Miscellaneous"] = {}
        if "Log" not in rpcs3ymlconfig:
            rpcs3ymlconfig["Log"] = {}

        # -= [Core] =-
        # Set the PPU Decoder based on config
        rpcs3ymlconfig["Core"]["PPU Decoder"] = system.get_option("rpcs3_ppudecoder", "Recompiler (LLVM)")
        # Set the SPU Decoder based on config
        rpcs3ymlconfig["Core"]["SPU Decoder"] = system.get_option("rpcs3_spudecoder", "Recompiler (LLVM)")
        # Set the SPU XFloat Accuracy based on config
        rpcs3ymlconfig["Core"]["XFloat Accuracy"] = system.get_option("rpcs3_spuxfloataccuracy", "Approximate")
        # Set the Default Core Values we need
        # Force to True for now to account for updates where exiting config file present. (True results in less stutter when a SPU module is in cache)
        rpcs3ymlconfig["Core"]["SPU Cache"] = True
        # Preferred SPU Threads
        rpcs3ymlconfig["Core"]["Preferred SPU Threads"] = system.get_option("rpcs3_sputhreads", 0)
        # SPU Loop Detection
        rpcs3ymlconfig["Core"]["SPU loop detection"] = system.get_option("rpcs3_spuloopdetection", False)
        # SPU Block Size
        rpcs3ymlconfig["Core"]["SPU Block Size"] = system.get_option("rpcs3_spublocksize", "Safe")
        # Max Power Saving CPU-Preemptions
        # values are maximum yields per frame threshold
        rpcs3ymlconfig["Core"]["Max CPU Preempt Count"] = system.get_option("rpcs3_maxcpu_preemptcount", 0)

        # -= [Video] =-
        # gfx backend - default to Vulkan
        # Check Vulkan first to be sure
        if vulkan.is_available():
            _logger.debug("Vulkan driver is available on the system.")
            if system.get_option("rpcs3_gfxbackend") == "OpenGL":
                _logger.debug("User selected OpenGL")
                rpcs3ymlconfig["Video"]["Renderer"] = "OpenGL"
            else:
                rpcs3ymlconfig["Video"]["Renderer"] = "Vulkan"

            if vulkan.has_discrete_gpu():
                _logger.debug("A discrete GPU is available on the system. We will use that for performance")
                discrete_name = vulkan.get_discrete_gpu_name()
                if discrete_name:
                    _logger.debug("Using Discrete GPU Name: %s for RPCS3", discrete_name)
                    if "Vulkan" not in rpcs3ymlconfig["Video"]:
                        rpcs3ymlconfig["Video"]["Vulkan"] = {}
                    rpcs3ymlconfig["Video"]["Vulkan"]["Adapter"] = discrete_name
                else:
                    _logger.debug("Couldn't get discrete GPU Name")
            else:
                _logger.debug("Discrete GPU is not available on the system. Using default.")
        else:
            _logger.debug("Vulkan driver is not available on the system. Falling back to OpenGL")
            rpcs3ymlconfig["Video"]["Renderer"] = "OpenGL"

        # System aspect ratio (the setting in the PS3 system itself, not the displayed ratio) a.k.a. TV mode.
        # If not set, see if the screen ratio is closer to 4:3 or 16:9 and pick that.
        rpcs3ymlconfig["Video"]["Aspect ratio"] = ratio if (ratio := system.get_option("rpcs3_ratio")) else ":".join(Rpcs3Generator.getClosestRatio(gameResolution))
        # Shader compilation
        rpcs3ymlconfig["Video"]["Shader Mode"] = system.get_option("rpcs3_shadermode", "Async Shader Recompiler")
        # Vsync
        rpcs3ymlconfig["Video"]["VSync"] = system.get_option("rpcs3_vsync", False)
        # Stretch to display area
        rpcs3ymlconfig["Video"]["Stretch To Display Area"] = system.get_option("rpcs3_stretchdisplay", False)
        # Frame Limit
        # Frame limit checks for specific values("Auto", "Off", "30", "50", "59.94", "60")
        # Second Frame Limit can be any float/integer. 0 = disabled.
        if (framelimit := system.get_option("rpcs3_framelimit")) is not system.MISSING:
            # Check for valid Frame Limit value, if it's not a Frame Limit value apply to Second Frame Limit
            if framelimit in ["Off", "30", "50", "59.94", "60"]:
                rpcs3ymlconfig["Video"]["Frame limit"] = framelimit
                rpcs3ymlconfig["Video"]["Second Frame Limit"] = 0
            else:
                rpcs3ymlconfig["Video"]["Second Frame Limit"] = framelimit
                rpcs3ymlconfig["Video"]["Frame limit"] = "Off"
        else:
            rpcs3ymlconfig["Video"]["Frame limit"] = "Auto"
            rpcs3ymlconfig["Video"]["Second Frame Limit"] = 0
        # Write Color Buffers
        rpcs3ymlconfig["Video"]["Write Color Buffers"] = system.get_option("rpcs3_colorbuffers", False)
        # Disable Vertex Cache
        rpcs3ymlconfig["Video"]["Disable Vertex Cache"] = system.get_option("rpcs3_vertexcache", False)
        # Anisotropic Filtering
        rpcs3ymlconfig["Video"]["Anisotropic Filter Override"] = system.get_option("rpcs3_anisotropic", 0)
        # MSAA
        rpcs3ymlconfig["Video"]["MSAA"] = system.get_option("rpcs3_aa", "Auto")
        # ZCULL
        match system.get_option("rpcs3_zcull"):
            case "Approximate":
                rpcs3ymlconfig["Video"]["Accurate ZCULL stats"] = False
                rpcs3ymlconfig["Video"]["Relaxed ZCULL Sync"] = False
            case "Relaxed":
                rpcs3ymlconfig["Video"]["Accurate ZCULL stats"] = False
                rpcs3ymlconfig["Video"]["Relaxed ZCULL Sync"] = True
            case _:
                rpcs3ymlconfig["Video"]["Accurate ZCULL stats"] = True
                rpcs3ymlconfig["Video"]["Relaxed ZCULL Sync"] = False
        # Shader Precision
        rpcs3ymlconfig["Video"]["Shader Precision"] = system.get_option("rpcs3_shader", "High")
        # Internal resolution (CHANGE AT YOUR OWN RISK)
        rpcs3ymlconfig["Video"]["Resolution"] = "1280x720"
        # Resolution scaling
        rpcs3ymlconfig["Video"]["Resolution Scale"] = system.get_option("rpcs3_resolution_scale", "100")
        # Output Scaling
        rpcs3ymlconfig["Video"]["Output Scaling Mode"] = system.get_option("rpcs3_scaling", "Bilinear")
        # Number of Shader Compilers
        rpcs3ymlconfig["Video"]["Shader Compiler Threads"] = system.get_option("rpcs3_num_compilers", 0)
        # Multithreaded RSX
        rpcs3ymlconfig["Video"]["Multithreaded RSX"] = system.get_option("rpcs3_rsx", False)
        # Async Texture Streaming
        rpcs3ymlconfig["Video"]["Asynchronous Texture Streaming 2"] = system.get_option("rpcs3_async_texture", False)

        # -= [Audio] =-
        # defaults
        rpcs3ymlconfig["Audio"]["Renderer"] = "Cubeb"
        rpcs3ymlconfig["Audio"]["Master Volume"] = 100
        # audio format
        rpcs3ymlconfig["Audio"]["Audio Format"] = system.get_option("rpcs3_audio_format", "Automatic")
        # convert to 16 bit
        rpcs3ymlconfig["Audio"]["Convert to 16 bit"] = system.get_option_bool("rpcs3_audio_16bit")
        # audio buffering
        rpcs3ymlconfig["Audio"]["Enable Buffering"] = system.get_option("rpcs3_audiobuffer", True)
        # audio buffer duration
        rpcs3ymlconfig["Audio"]["Desired Audio Buffer Duration"] = system.get_option_int("rpcs3_audiobuffer_duration", 100)
        # time stretching
        if system.get_option_bool("rpcs3_timestretch"):
            rpcs3ymlconfig["Audio"]["Enable Time Stretching"] = True
            rpcs3ymlconfig["Audio"]["Enable Buffering"] = True
        else:
            rpcs3ymlconfig["Audio"]["Enable Time Stretching"] = False
        # time stretching threshold
        rpcs3ymlconfig["Audio"]["Time Stretching Threshold"] = system.get_option_int("rpcs3_timestretch_threshold", 75)

        # -= [Input/Output] =-
        # gun stuff
        if system.get_option_bool("use_guns") and guns:
            rpcs3ymlconfig["Input/Output"]["Move"] = "Gun"
            rpcs3ymlconfig["Input/Output"]["Camera"] = "Fake"
            rpcs3ymlconfig["Input/Output"]["Camera type"] = "PS Eye"
        # Gun crosshairs
        rpcs3ymlconfig["Input/Output"]["Show move cursor"] = system.get_option("rpcs3_crosshairs", False)

        # -= [Miscellaneous] =-
        rpcs3ymlconfig["Miscellaneous"]["Exit RPCS3 when process finishes"] = True
        rpcs3ymlconfig["Miscellaneous"]["Start games in fullscreen mode"] = True
        rpcs3ymlconfig["Miscellaneous"]["Show shader compilation hint"] = False
        rpcs3ymlconfig["Miscellaneous"]["Prevent display sleep while running games"] = True
        rpcs3ymlconfig["Miscellaneous"]["Show trophy popups"] = False

        with RPCS3_CONFIG.open("w") as file:
            yaml = YAML(pure=True)
            yaml.default_flow_style = False
            yaml.dump(rpcs3ymlconfig, file)

        # copy icon files to config
        icon_target = RPCS3_CONFIG_DIR / 'Icons'
        mkdir_if_not_exists(icon_target)
        shutil.copytree('/usr/share/rpcs3/Icons/', icon_target, dirs_exist_ok=True, copy_function=shutil.copy2)

        # determine the rom name
        if rom.suffix == ".psn":
            with rom.open() as fp:
                for line in fp:
                    if len(line) >= 9:
                        romName = RPCS3_CONFIG_DIR / "dev_hdd0" / "game" / line.strip().upper() / "USRDIR" / "EBOOT.BIN"
        else:
            romName = rom / "PS3_GAME" / "USRDIR" / "EBOOT.BIN"

        # write our own gamecontrollerdb.txt file before launching the game
        dbfile = RPCS3_CONFIG_DIR / "input_configs" / "gamecontrollerdb.txt"
        write_sdl_controller_db(playersControllers, dbfile)

        commandArray = [RPCS3_BIN, romName]

        if not system.get_option_bool("rpcs3_gui"):
            commandArray.append("--no-gui")

        # firmware not installed and available : instead of starting the game, install it
        if Rpcs3Generator.getFirmwareVersion() is None and (ps3updat := (BIOS / "PS3UPDAT.PUP")).exists():
            commandArray = [RPCS3_BIN, "--installfw", ps3updat]

        return Command.Command(
            array=commandArray,
            env={
                "XDG_CONFIG_HOME":CONFIGS,
                "XDG_CACHE_HOME":CACHE,
                "QT_QPA_PLATFORM":"xcb",
                "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers),
                "SDL_JOYSTICK_HIDAPI": "0"
            }
        )

    @staticmethod
    def getClosestRatio(gameResolution: Resolution) -> tuple[str, str]:
        screenRatio = gameResolution["width"] / gameResolution["height"]

        if screenRatio < 1.6:
            return ('4','3')

        return ('16','9')

    def getInGameRatio(self, config, gameResolution, rom):
        return 16/9

    @staticmethod
    def getFirmwareVersion():
        try:
            with (RPCS3_CONFIG_DIR / "dev_flash" / "vsh" / "etc" / "version.txt").open("r") as stream:
                for line in stream:
                    matches = re.match("^release:(.*):", line)
                    if matches:
                        return matches[1]
        except Exception:
            return None
        return None
