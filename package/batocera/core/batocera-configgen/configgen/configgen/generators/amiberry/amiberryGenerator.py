from __future__ import annotations

import logging
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING, Final

from ... import Command
from ...batoceraPaths import CONFIGS, mkdir_if_not_exists
from ...controller import generate_sdl_game_controller_config
from ...settings.unixSettings import UnixSettings
from ..Generator import Generator
from ..libretro import libretroControllers

if TYPE_CHECKING:
    from ...types import HotkeysContext

_logger = logging.getLogger(__name__)

_CONFIG_DIR: Final = CONFIGS / 'amiberry'
_CONFIG: Final = _CONFIG_DIR / 'conf' / 'amiberry.conf'
_RETROARCH_CUSTOM: Final = _CONFIG_DIR / 'conf' / 'retroarch' / 'overlay.cfg'
_RETROARCH_INPUTS_DIR: Final = _CONFIG_DIR / 'conf' / 'retroarch' / 'inputs'

class AmiberryGenerator(Generator):

    def getHotkeysContext(self) -> HotkeysContext:
        return {
            "name": "amiberry",
            "keys": { "exit": "KEY_F10" }
        }

    def generate(self, system, rom, playersControllers, metadata, guns, wheels, gameResolution):
        mkdir_if_not_exists(_RETROARCH_CUSTOM.parent)

        retroconfig = UnixSettings(_RETROARCH_CUSTOM, separator=' ')
        amiberryconf = UnixSettings(_CONFIG, separator=' ')
        amiberryconf.save('default_quit_key', 'F10')
        amiberryconf.save('saveimage_dir', '/userdata/saves/amiga/')
        amiberryconf.save('savestate_dir', '/userdata/saves/amiga/')
        amiberryconf.save('screenshot_dir', '/userdata/screenshots/')
        amiberryconf.save('rom_path', '/userdata/bios/amiga/')
        amiberryconf.save('whdboot_path', '/usr/share/amiberry/whdboot/')
        amiberryconf.save('logfile_path', '/userdata/system/logs/amiberry.log')
        amiberryconf.save('controllers_path', '/userdata/system/configs/amiberry/conf/retroarch/inputs/')
        amiberryconf.save('retroarch_config', _RETROARCH_CUSTOM)
        amiberryconf.save('default_vkbd_enabled', 'yes')
        amiberryconf.save('default_vkbd_hires', 'yes') # TODO: make an option in ES
        amiberryconf.save('default_vkbd_transparency', '60') # TODO: make an option in ES
        amiberryconf.save('default_vkbd_toggle', 'leftstick')
        amiberryconf.write()

        romType = self.getRomType(rom)
        _logger.debug("romType: %s", romType)
        if romType != 'UNKNOWN' :
            commandArray: list[str | Path] = [ "/usr/bin/amiberry", "-G" ]
            if romType != 'WHDL' :
                commandArray.extend(["--model", system.core])

            if romType == 'WHDL' :
                commandArray.extend(["--autoload", rom])
            elif romType == 'HDF' :
                commandArray.extend([
                    "-s", f"hardfile2=rw,DH0:{rom},32,1,2,512,0,,uae0",
                    "-s", f"uaehf0=hdf,rw,DH0:{rom},32,1,2,512,0,,uae0",
                ])
            elif romType == 'CD' :
                commandArray.extend(["--cdimage", rom])
            elif romType == 'DISK':
                # floppies
                for n, img in enumerate(self.floppiesFromRom(rom)):
                    if n < 4:
                        commandArray.extend([f"-{n}", img])
                # floppy path
                commandArray.extend([
                    "-s",
                    # Use disk folder as floppy path
                    f"amiberry.floppy_path={rom.parent}",
                ])

            # controller
            libretroControllers.writeControllersConfig(retroconfig, system, playersControllers, True)
            retroconfig.write()

            mkdir_if_not_exists(_RETROARCH_INPUTS_DIR)

            for nplayer, pad in enumerate(sorted(playersControllers.values()), start=1):
                replacements = {'_player' + str(nplayer) + '_':'_'}
                # amiberry remove / included in pads names like "USB Downlo01.80 PS3/USB Corded Gamepad"
                padfilename = pad.real_name.replace("/", "")
                playerInputFilename = _RETROARCH_INPUTS_DIR / f"{padfilename}.cfg"
                with _RETROARCH_CUSTOM.open() as infile, playerInputFilename.open('w') as outfile:
                    for line in infile:
                        for src, target in replacements.items():
                            newline = line.replace(src, target)
                            if not newline.isspace():
                                outfile.write(newline)
                if nplayer == 1: # 1 = joystick port
                    commandArray.extend(["-s", "joyport1_friendlyname=" + padfilename])
                    if romType == 'CD' :
                        commandArray.extend(["-s", "joyport1_mode=cd32joy"])
                if nplayer == 2: # 0 = mouse for the player 2
                    commandArray.extend(["-s", "joyport0_friendlyname=" + padfilename])

            # fps
            if system.show_fps:
                commandArray.extend(["-s", "show_leds=true"])

            commandArray.extend([
                # disable port 2 (otherwise, the joystick goes on it)
                "-s",
                "joyport2=",

                # remove interlace artifacts
                "-s",
                f"gfx_flickerfixer={'true' if system.get_option_bool('amiberry_flickerfixer') else 'false'}",

                # auto height
                "-s",
                f"amiberry.gfx_auto_height={'true' if system.get_option_bool('amiberry_auto_height') else 'false'}",
            ])

            # line mode
            linemode = system.get_option_str("amiberry_linemode", "double")
            if linemode in ['none', 'scanlines', 'double']:
                commandArray.extend(["-s", f"gfx_linemode={linemode}"])

            # video resolution
            resolution = system.get_option_str("amiberry_resolution", "hires")
            if resolution in ['lores', 'superhires', 'hires']:
                commandArray.extend(["-s", f"gfx_resolution={resolution}"])

            # Scaling method
            scaling_method = system.get_option_str("amiberry_scalingmethod", "automatic")
            if scaling_method == 'automatic':
                commandArray.extend([
                    "-s", "gfx_lores_mode=false",
                    "-s", "amiberry.scaling_method=-1",
                ])
            elif scaling_method == 'smooth':
                commandArray.extend([
                    "-s", "gfx_lores_mode=true",
                    "-s", "amiberry.scaling_method=1",
                ])
            elif scaling_method == 'pixelated':
                commandArray.extend([
                    "-s", "gfx_lores_mode=true",
                    "-s", "amiberry.scaling_method=0",
                ])

            commandArray.extend([
                # display vertical centering
                "-s",
                "gfx_center_vertical=smart",

                # fix sound buffer and frequency
                "-s",
                "sound_max_buff=4096",
                "-s",
                "sound_frequency=48000",
            ])

            return Command.Command(array=commandArray,env={
                "AMIBERRY_DATA_DIR": "/usr/share/amiberry/",
                "AMIBERRY_HOME_DIR": "/userdata/system/configs/amiberry/",
                "SDL_GAMECONTROLLERCONFIG": generate_sdl_game_controller_config(playersControllers)})
        # otherwise, unknown format
        return Command.Command(array=[])

    def floppiesFromRom(self, rom: Path):
        floppies: list[Path] = []
        indexDisk = rom.name.rfind("(Disk 1")

        # from one file (x1.zip), get the list of all existing files with the same extension + last char (as number) suffix
        # for example, "/path/toto0.zip" becomes ["/path/toto0.zip", "/path/toto1.zip", "/path/toto2.zip"]
        if rom.stem[-1:].isdigit():
            # path without the number
            fileprefix = rom.stem[:-1]

            # special case for 0 while numerotation can start at 1
            zero_file = rom.with_name(f"{fileprefix}0{rom.suffix}")
            if zero_file.is_file():
                floppies.append(zero_file)

            # adding all other files
            n = 1
            while (floppy := rom.with_name(f"{fileprefix}{n}{rom.suffix}")).is_file():
                floppies.append(floppy)
                n += 1
        # (Disk 1 of 2) format
        elif indexDisk != -1:
                # Several disks
                floppies.append(rom)
                prefix = rom.name[0:indexDisk+6]
                postfix = rom.name[indexDisk+7:]
                n = 2
                while (floppy := rom.with_name(f"{prefix}{n}{postfix}")).is_file():
                    floppies.append(floppy)
                    n += 1
        else:
            #Single ADF
            return [rom]

        return floppies

    def getRomType(self, filepath: Path):
        extension = filepath.suffix[1:].lower()

        if extension == "lha":
            return 'WHDL'
        if extension == 'hdf' :
            return 'HDF'
        if extension in ['iso','cue', 'chd'] :
            return 'CD'
        if extension in ['adf','ipf']:
            return 'DISK'
        if extension == "zip":
            # can be either whdl or adf
            with zipfile.ZipFile(filepath) as zip:
                for zipfilename in zip.namelist():
                    if zipfilename.find('/') == -1: # at the root
                        extension = Path(zipfilename).suffix[1:]
                        if extension == "info":
                            return 'WHDL'
                        if extension == 'lha' :
                            _logger.warning("Amiberry doesn't support .lha inside a .zip")
                            return 'UNKNOWN'
                        if extension == 'adf' :
                            return 'DISK'
            # no info or adf file found
            return 'UNKNOWN'

        return 'UNKNOWN'
