from __future__ import annotations

from shutil import copyfile
from typing import TYPE_CHECKING

from ... import Command
from ...batoceraPaths import CONFIGS, ensure_parents_and_open, mkdir_if_not_exists
from ...controller import generate_sdl_game_controller_config
from ...utils.configparser import CaseSensitiveConfigParser
from ..Generator import Generator
from . import flycastControllers
from .flycastPaths import FLYCAST_BIOS, FLYCAST_CONFIG, FLYCAST_SAVES, FLYCAST_VMU_BLANK, FLYCAST_VMUA1, FLYCAST_VMUA2

if TYPE_CHECKING:
    from ...types import HotkeysContext


class FlycastGenerator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "flycast",
            "keys": {
                "exit": "KEY_F7",
                "menu": "KEY_TAB",
                "save_state": "KEY_F8",
                "restore_state": "KEY_F9"
            }
        }

    # Main entry of the module
    # Configure fba and return a command
    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        # Write emu.cfg to map joysticks, init with the default emu.cfg
        Config = CaseSensitiveConfigParser(interpolation=None)
        if FLYCAST_CONFIG.exists():
            try:
                Config.read(FLYCAST_CONFIG)
            except Exception:
                pass # give up the file

        if not Config.has_section("input"):
            Config.add_section("input")
        # For each pad detected
        for index in playersControllers:
            controller = playersControllers[index]
            # Write the mapping files for Dreamcast
            if (system.name == "dreamcast"):
                flycastControllers.generateControllerConfig(controller, "dreamcast")
            else:
                # Write the Arcade variant (Atomiswave & Naomi/2)
                flycastControllers.generateControllerConfig(controller, "arcade")

            # Set the controller type per Port
            Config.set("input", f'device{controller.player_number}', "0") # Sega Controller
            Config.set("input", f'device{controller.player_number}.1', "1") # Sega VMU
            # Set controller pack, gui option
            Config.set("input", f'device{controller.player_number}.2', system.get_option_str(f"flycast_ctrl{controller.player_number}_pack", "1"))
            # Ensure controller(s) are on seperate Ports
            port = controller.player_number-1
            Config.set("input", f'maple_sdl_joystick_{port}', str(port))

        # add the keyboard mappings for hotkeys
        flycastControllers.generateKeyboardConfig()

        if not Config.has_section("config"):
            Config.add_section("config")
        if not Config.has_section("window"):
            Config.add_section("window")
        # ensure we are always fullscreen
        Config.set("window", "fullscreen", "yes")
        # set video resolution
        Config.set("window", "width", str(gameResolution["width"]))
        Config.set("window", "height", str(gameResolution["height"]))
        # set render resolution - default 480 (Native)
        Config.set("config", "rend.Resolution", system.get_option_str("flycast_render_resolution", "480"))
        # wide screen mode - default off
        Config.set("config", "rend.WideScreen", system.get_option_str("flycast_ratio", "no"))
        # rotate option - default off
        Config.set("config", "rend.Rotate90", system.get_option_str("flycast_rotate", "no"))
        # renderer - default: OpenGL
        renderer = system.get_option('flycast_renderer')
        sorting = system.get_option('flycast_sorting')
        if renderer == "0":
            if sorting == "3":
                # per pixel
                Config.set("config", "pvr.rend", "3")
            else:
                # per triangle
                Config.set("config", "pvr.rend", "0")
        elif renderer == "4":
            if sorting == "3":
                # per pixel
                Config.set("config", "pvr.rend", "5")
            else:
                # per triangle
                Config.set("config", "pvr.rend", "4")
        else:
            Config.set("config", "pvr.rend", "0")
            if sorting == "3":
                # per pixel
                Config.set("config", "pvr.rend", "3")
        # anisotropic filtering
        Config.set("config", "rend.AnisotropicFiltering", system.get_option_str("flycast_anisotropic", "1"))
        # transparent sorting
        # per strip
        Config.set("config", "rend.PerStripSorting", "yes" if sorting == "2" else "no")

        # [Dreamcast specifics]
        # language
        Config.set("config", "Dreamcast.Language", system.get_option_str("flycast_language", "1"))
        # region
        Config.set("config", "Dreamcast.Region", system.get_option_str("flycast_region", "1"))
        # save / load states
        Config.set("config", "Dreamcast.AutoLoadState", system.get_option_str("flycast_loadstate", "no"))
        Config.set("config", "Dreamcast.AutoSaveState", system.get_option_str("flycast_savestate", "no"))
        # windows CE
        Config.set("config", "Dreamcast.ForceWindowsCE", system.get_option_str("flycast_winCE", "no"))
        # DSP
        Config.set("config", "aica.DSPEnabled", system.get_option_str("flycast_DSP", "no"))
        # Guns (WIP)
        # Guns crosshairs
        Config.set("config", "rend.CrossHairColor1", system.get_option_str("flycast_lightgun1_crosshair", "0"))
        Config.set("config", "rend.CrossHairColor2", system.get_option_str("flycast_lightgun2_crosshair", "0"))
        Config.set("config", "rend.CrossHairColor3", system.get_option_str("flycast_lightgun3_crosshair", "0"))
        Config.set("config", "rend.CrossHairColor4", system.get_option_str("flycast_lightgun4_crosshair", "0"))

        # Retroachievements
        if not Config.has_section("achievements"):
            Config.add_section("achievements")

        if system.get_option_bool('retroachievements'):
            headers   = {"Content-type": "text/plain", "User-Agent": "Batocera.linux"}
            login_url = "https://retroachievements.org/"
            username  = system.get_option_str('retroachievements.username', "")
            password  = system.get_option_str('retroachievements.password', "")
            hardcore  = system.get_option_str('retroachievements.hardcore', "")
            token     = system.get_option_str('retroachievements.token', "")
            # apply config
            Config.set("achievements", "Enabled", "yes")
            if hardcore == '1':
                Config.set("achievements", "HardcoreMode", "yes")
            else:
                Config.set("achievements", "HardcoreMode", "no")
            Config.set("achievements", "Token", token)
            Config.set("achievements", "UserName" , username)
        else:
            Config.set("achievements", "Enabled", "no")

        # custom : allow the user to configure directly emu.cfg via batocera.conf via lines like : dreamcast.flycast.section.option=value
        for section_option, value in system.option_items(starts_with="flycast."):
            section_option_splitter = section_option.find(".")
            custom_section = section_option[:section_option_splitter]
            custom_option = section_option[section_option_splitter+1:]
            if not Config.has_section(custom_section):
                Config.add_section(custom_section)
            Config.set(custom_section, custom_option, value)

        ### update the configuration file
        with ensure_parents_and_open(FLYCAST_CONFIG, 'w+') as cfgfile:
            Config.write(cfgfile)
            cfgfile.close()

        # internal config
        mkdir_if_not_exists(FLYCAST_SAVES)

        # vmuA1
        if not FLYCAST_VMUA1.is_file():
            copyfile(FLYCAST_VMU_BLANK, FLYCAST_VMUA1)
        # vmuA2
        if not FLYCAST_VMUA2.is_file():
            copyfile(FLYCAST_VMU_BLANK, FLYCAST_VMUA2)

        # the command to run
        commandArray = ['/usr/bin/flycast', rom]
        # Here is the trick to make flycast find files :
        # emu.cfg is in $XDG_CONFIG_DIRS or $XDG_CONFIG_HOME.
        # VMU will be in $XDG_DATA_HOME / $FLYCAST_DATADIR because it needs rw access -> /userdata/saves/dreamcast
        # $FLYCAST_BIOS_PATH is where Flaycast should find the bios files
        # controller cfg files are set with an absolute path, so no worry
        return Command.Command(
            array=commandArray,
            env={
                "XDG_CONFIG_HOME":CONFIGS,
                "XDG_CONFIG_DIRS":CONFIGS,
                "XDG_DATA_HOME":FLYCAST_SAVES.parent,
                "FLYCAST_DATADIR":FLYCAST_SAVES.parent,
                "FLYCAST_BIOS_PATH":FLYCAST_BIOS,
                "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers),
                "SDL_JOYSTICK_HIDAPI": "0"
            }
        )
