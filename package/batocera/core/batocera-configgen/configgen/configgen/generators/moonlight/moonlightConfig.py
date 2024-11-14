from __future__ import annotations

import shutil
from typing import TYPE_CHECKING

from ...batoceraPaths import mkdir_if_not_exists
from ...settings.unixSettings import UnixSettings
from .moonlightPaths import MOONLIGHT_CONFIG, MOONLIGHT_CONFIG_DIR, MOONLIGHT_STAGING_CONFIG, MOONLIGHT_STAGING_DIR

if TYPE_CHECKING:
    from ...Emulator import Emulator


def generateMoonlightConfig(system: Emulator):

    mkdir_if_not_exists(MOONLIGHT_STAGING_DIR)

    # If user made config file exists, copy to staging directory for use
    if MOONLIGHT_CONFIG.exists():
        shutil.copy(MOONLIGHT_CONFIG, MOONLIGHT_STAGING_CONFIG)
    else:
        # truncate existing config and create new one
        with MOONLIGHT_STAGING_CONFIG.open("w"):
            pass

        moonlightConfig = UnixSettings(MOONLIGHT_STAGING_CONFIG, separator=' ')

        # resolution
        if resolution := system.get_option('moonlight_resolution'):
            if resolution == "0":
                moonlightConfig.save('width', '1280')
                moonlightConfig.save('height', '720')
            elif resolution == "1":
                moonlightConfig.save('width', '1920')
                moonlightConfig.save('height', '1080')
            elif resolution == "2":
                moonlightConfig.save('width', '3840')
                moonlightConfig.save('height', '2160')
        else:
            moonlightConfig.save('width', '1280')
            moonlightConfig.save('height', '720')

        # rotate
        moonlightConfig.save('rotate', system.get_option('moonlight_rotate', '0'))

        # framerate
        if framerate := system.get_option('moonlight_framerate'):
            if framerate == "0":
                moonlightConfig.save('fps', '30')
            elif framerate == "1":
                moonlightConfig.save('fps', '60')
            elif framerate == "2":
                moonlightConfig.save('fps', '120')
        else:
            moonlightConfig.save('fps', '60')

        # bitrate
        if bitrate := system.get_option('moonlight_bitrate'):
            if bitrate == "0":
                moonlightConfig.save('bitrate', '5000')
            elif bitrate == "1":
                moonlightConfig.save('bitrate', '10000')
            elif bitrate == "2":
                moonlightConfig.save('bitrate', '20000')
            elif bitrate == "3":
                moonlightConfig.save('bitrate', '50000')
        else:
            moonlightConfig.save('bitrate', '-1') #-1 sets Moonlight default

        # codec
        moonlightConfig.save('codec', system.get_option('moonlight_codec', 'auto'))

        # sops (Streaming Optimal Playable Settings)
        moonlightConfig.save('sops', system.get_option_str('moonlight_sops', 'true').lower())

        # quit remote app on exit
        moonlightConfig.save('quitappafter', system.get_option_str('moonlight_quitapp', 'false').lower())

        # view only
        moonlightConfig.save('viewonly', system.get_option_str('moonlight_viewonly', 'false').lower())

        # platform - we only select sdl (best compatibility)
        # required for controllers to work
        moonlightConfig.save('platform', 'sdl')

        ## Directory to store encryption keys
        moonlightConfig.save('keydir', MOONLIGHT_CONFIG_DIR / 'keydir')

        # lan or wan streaming - ideally lan
        moonlightConfig.save('remote', system.get_option('moonlight_remote', 'no'))

        ## Enable 5.1/7.1 surround sound
        moonlightConfig.save('surround', system.get_option('moonlight_surround', '5.1'))

        moonlightConfig.write()
