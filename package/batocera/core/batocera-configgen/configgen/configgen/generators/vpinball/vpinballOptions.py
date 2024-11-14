from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...Emulator import Emulator
    from ...utils.configparser import CaseSensitiveConfigParser


def configureOptions(vpinballSettings: CaseSensitiveConfigParser, system: Emulator) -> None:
    # Tables are organised by folders containing the vpx file, and sub-folders with the roms, altcolor, altsound,...
    # We keep a switch to allow users with the old unique pinmame to be able to continue using vpinball (switchon)
    vpinballSettings.set("Standalone", "PinMAMEPath", system.get_option_bool("vpinball_folders", True, return_values=("./", "")))

    # Ball trail
    if (balltrail := system.get_option("vpinball_balltrail")) is not system.MISSING:
        vpinballSettings.set("Player", "BallTrail", "1")
        vpinballSettings.set("Player", "BallTrailStrength", balltrail)
    else:
        vpinballSettings.set("Player", "BallTrail", "0")
        vpinballSettings.set("Player", "BallTrailStrength", "0")

    # Visual Nugde Strength
    vpinballSettings.set("Player", "NudgeStrength", system.get_option("vpinball_nudgestrength", ""))

    # Performance settings
    vpinballSettings.set("Player", "MaxFramerate", system.get_option("vpinball_maxframerate", ""))

    # vsync
    vpinballSettings.set("Player", "SyncMode", system.get_option("vpinball_vsync", "2"))

    # presets
    match system.get_option("vpinball_presets"):
        case "defaults":
            vpinballSettings.set("Player", "FXAA", "")
            vpinballSettings.set("Player", "Sharpen", "")
            vpinballSettings.set("Player", "DisableAO", "")
            vpinballSettings.set("Player", "DynamicAO", "")
            vpinballSettings.set("Player", "SSRefl", "")
            vpinballSettings.set("Player", "PFReflection", "")
            vpinballSettings.set("Player", "ForceAnisotropicFiltering", "")
            vpinballSettings.set("Player", "AlphaRampAccuracy", "")
        case "highend":
            vpinballSettings.set("Player", "FXAA", "3")
            vpinballSettings.set("Player", "Sharpen", "2")
            vpinballSettings.set("Player", "DisableAO", "0")
            vpinballSettings.set("Player", "DynamicAO", "1")
            vpinballSettings.set("Player", "SSRefl", "1")
            vpinballSettings.set("Player", "PFReflection", "5")
            vpinballSettings.set("Player", "ForceAnisotropicFiltering", "1")
            vpinballSettings.set("Player", "AlphaRampAccuracy", "10")
        case "lowend":
            vpinballSettings.set("Player", "FXAA", "0")
            vpinballSettings.set("Player", "Sharpen", "0")
            vpinballSettings.set("Player", "DisableAO", "1")
            vpinballSettings.set("Player", "DynamicAO", "0")
            vpinballSettings.set("Player", "SSRefl", "0")
            vpinballSettings.set("Player", "PFReflection", "3")
            vpinballSettings.set("Player", "ForceAnisotropicFiltering", "0")
            vpinballSettings.set("Player", "AlphaRampAccuracy", "5")
        case "manual":
            pass
        case system.MISSING: # like defaults
            vpinballSettings.set("Player", "FXAA", "")
            vpinballSettings.set("Player", "Sharpen", "")
            vpinballSettings.set("Player", "DisableAO", "")
            vpinballSettings.set("Player", "DynamicAO", "")
            vpinballSettings.set("Player", "SSRefl", "")
            vpinballSettings.set("Player", "PFReflection", "")
            vpinballSettings.set("Player", "ForceAnisotropicFiltering", "")
            vpinballSettings.set("Player", "AlphaRampAccuracy", "")

    # custom display physical setup
    if system.get_option_bool("vpinball_customphysicalsetup"):
        # Width
        vpinballSettings.set("Player", "ScreenWidth", system.get_option("vpinball_screenwidth", ""))
        # Height
        vpinballSettings.set("Player", "ScreenHeight", system.get_option("vpinball_screenheight", ""))
        # Inclination
        vpinballSettings.set("Player", "ScreenInclination", system.get_option("vpinball_screeninclination", ""))
        # Y
        vpinballSettings.set("Player", "ScreenPlayerY", system.get_option("vpinball_screenplayery", ""))
        # Z
        vpinballSettings.set("Player", "ScreenPlayerZ", system.get_option("vpinball_screenplayerz", ""))
    else:
        vpinballSettings.set("Player", "ScreenWidth",       "")
        vpinballSettings.set("Player", "ScreenHeight",      "")
        vpinballSettings.set("Player", "ScreenInclination", "")
        vpinballSettings.set("Player", "ScreenPlayerY",     "")
        vpinballSettings.set("Player", "ScreenPlayerZ",     "")

    # Altcolor (switchon)
    vpinballSettings.set("Standalone", "AltColor", system.get_option_bool("vpinball_altcolor", True, return_values=("1", "0")))

    # Sound balance
    vpinballSettings.set("Player", "MusicVolume", system.get_option("vpinball_musicvolume", ""))
    vpinballSettings.set("Player", "SoundVolume", system.get_option("vpinball_soundvolume", ""))

    # Altsound
    vpinballSettings.set("Standalone", "AltSound", system.get_option_bool("vpinball_altsound", True, return_values=("1", "0")))

    # select which ID for sounddevices by running:
    # /usr/bin/vpinball/VPinballX_GL -listsnd
    vpinballSettings.set("Player", "SoundDevice", system.get_option("vpinball_sounddevice", ""))
    vpinballSettings.set("Player", "SoundDeviceBG", system.get_option("vpinball_sounddevicebg", ""))

    # Don't use SDL "Add credit" with the South button/plunger and pad2key default mapping
    vpinballSettings.set("Player", "JoyAddCreditKey", system.get_option_bool("vpinball_pad_add_credit", return_values=("", "0")))
