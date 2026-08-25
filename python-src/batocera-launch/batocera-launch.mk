################################################################################
#
# batocera-launch
#
################################################################################

BATOCERA_LAUNCH_SETUP_TYPE=hatch
BATOCERA_LAUNCH_DEPENDENCIES = \
	python-batocera-common \
	python-evdev \
	python-pyudev \
	python-toml \
	python-pillow \
	python-qrcode

BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES =

ifeq ($(BR2_PACKAGE_ABUSE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += abuse.py
endif

ifeq ($(BR2_PACKAGE_BSTONE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += bstone.py
endif

ifeq ($(BR2_PACKAGE_CANNONBALL),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += cannonball.py
endif

ifeq ($(BR2_PACKAGE_CATACOMBGL),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += catacombgl.py
endif

ifeq ($(BR2_PACKAGE_CORSIXTH),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += corsixth.py
endif

ifeq ($(BR2_PACKAGE_DEVILUTIONX),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += devilutionx.py
endif

ifeq ($(BR2_PACKAGE_DHEWM3),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += dhewm3.py
endif

ifeq ($(BR2_PACKAGE_DOSBOX),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += dosbox.py
endif

ifeq ($(BR2_PACKAGE_DOSBOX_STAGING),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += dosbox_staging.py
endif

ifeq ($(BR2_PACKAGE_DOSBOX_X),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += dosboxx.py
endif

ifeq ($(BR2_PACKAGE_DXX_REBIRTH),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += dxx_rebirth.py
endif

ifeq ($(BR2_PACKAGE_EASYRPG_PLAYER),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += easyrpg.py
endif

ifeq ($(BR2_PACKAGE_ECWOLF),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += ecwolf.py
endif

ifeq ($(BR2_PACKAGE_EDUKE32),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += eduke32.py
endif

ifeq ($(BR2_PACKAGE_ETLEGACY),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += etlegacy.py
endif

ifeq ($(BR2_PACKAGE_FLATPAK),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += flatpak.py
endif

ifeq ($(BR2_PACKAGE_GSPLUS),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += gsplus.py
endif

ifeq ($(BR2_PACKAGE_HCL),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += hcl.py
endif

ifeq ($(BR2_PACKAGE_HURRICAN),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += hurrican.py
endif

ifeq ($(BR2_PACKAGE_IKEMEN),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += ikemen.py
endif

ifeq ($(BR2_PACKAGE_IORTCW),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += iortcw.py
endif

ifeq ($(BR2_PACKAGE_JAZZ2_NATIVE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += jazz2_native.py
endif

ifeq ($(BR2_PACKAGE_LIGHTSPARK),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += lightspark.py
endif

ifeq ($(BR2_PACKAGE_NANOBOYADVANCE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += nanoboyadvance.py
endif

ifeq ($(BR2_PACKAGE_OD_COMMANDER),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += odcommander.py
endif

ifeq ($(BR2_PACKAGE_BATOCERA_PYGAME),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += pygame.py
endif

ifeq ($(BR2_PACKAGE_PYTHON_PYXEL),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += pyxel.py
endif

ifeq ($(BR2_PACKAGE_RAZE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += raze.py
endif

ifeq ($(BR2_PACKAGE_RUFFLE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += ruffle.py
endif

ifeq ($(BR2_PACKAGE_SIMCOUPE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += samcoupe.py
endif

ifeq ($(BR2_PACKAGE_SCUMMVM),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += scummvm.py
endif

ifeq ($(BR2_PACKAGE_SDLPOP),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += sdlpop.py
endif

ifeq ($(BR2_PACKAGE_SOLARUS_ENGINE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += solarus.py
endif

ifeq ($(BR2_PACKAGE_SONIC3_AIR),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += sonic3_air.py
endif

ifeq ($(BR2_PACKAGE_SONIC_MANIA),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += sonic_mania.py
endif

ifeq ($(BR2_PACKAGE_SONIC2013)$(BR2_PACKAGE_SONICCD),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += sonicretro.py
endif

ifeq ($(BR2_PACKAGE_BATOCERA_STEAM),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += steam.py
endif

ifeq ($(BR2_PACKAGE_STELLA),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += stella.py
endif

ifeq ($(BR2_PACKAGE_TARADINO),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += taradino.py
endif

ifeq ($(BR2_PACKAGE_THEFORCEENGINE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += theforceengine.py
endif

ifeq ($(BR2_PACKAGE_THEXTECH),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += thextech.py
endif

ifeq ($(BR2_PACKAGE_TIC80),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += tic80.py
endif

ifeq ($(BR2_PACKAGE_TRX),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += trx.py
endif

ifeq ($(BR2_PACKAGE_TSUGARU),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += tsugaru.py
endif

ifeq ($(BR2_PACKAGE_TYRIAN),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += tyrian.py
endif

ifeq ($(BR2_PACKAGE_UQM),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += uqm.py
endif

ifeq ($(BR2_PACKAGE_VKQUAKE),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += vkquake.py
endif

ifeq ($(BR2_PACKAGE_VKQUAKE2),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += vkquake2.py
endif

ifeq ($(BR2_PACKAGE_X16EMU),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += x16emu.py
endif

ifeq ($(BR2_PACKAGE_XASH3D_FWGS),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += xash3d_fwgs/
endif

ifeq ($(BR2_PACKAGE_XROAR),)
BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES += xroar.py
endif

BATOCERA_LAUNCH_LOCAL_PYTHON_EXCLUSIONS = $(addprefix batocera_launch/emulators/,$(BATOCERA_LAUNCH_EXCLUDED_EMULATOR_MODULES))

define BATOCERA_LAUNCH_INSTALL_TARGET_DEFAULT_OPTIONS
	mkdir -p $(TARGET_DIR)/usr/share/batocera/launch/defaults
	$(INSTALL) -D -m 0644 $(@D)/resources/defaults/config.yml \
	    $(TARGET_DIR)/usr/share/batocera/launch/defaults/config.yml

	if test -e $(@D)/resources/defaults/config-$(BR2_BATOCERA_LAUNCH_ARCH).yml; then \
		$(INSTALL) -D -m 0644 $(@D)/resources/defaults/config-$(BR2_BATOCERA_LAUNCH_ARCH).yml \
		    $(TARGET_DIR)/usr/share/batocera/launch/defaults/config-arch.yml \
	fi
endef

define BATOCERA_LAUNCH_INSTALL_STAGING_DEFAULT_OPTIONS
	mkdir -p $(STAGING_DIR)/usr/share/batocera/launch
	$(INSTALL) -D -m 0644 $(@D)/resources/defaults/config.yml \
	    $(STAGING_DIR)/usr/share/batocera/launch/defaults/config.yml

	if test -e $(@D)/resources/defaults/config-$(BR2_BATOCERA_LAUNCH_ARCH).yml; then \
		$(INSTALL) -D -m 0644 $(@D)/resources/defaults/config-$(BR2_BATOCERA_LAUNCH_ARCH).yml \
		    $(STAGING_DIR)/usr/share/batocera/launch/defaults/config-arch.yml \
	fi
endef

define BATOCERA_LAUNCH_INSTALL_RESOURCES
	mkdir -p $(TARGET_DIR)/usr/share/batocera/launch/scripts
	mkdir -p $(TARGET_DIR)/usr/share/evmapy

	$(INSTALL) -D -m 0644 -t $(TARGET_DIR)/usr/share/batocera/launch/data \
		$(@D)/resources/data/gamesbuttonsdb.xml

	$(INSTALL) -D -m 0644 -t $(TARGET_DIR)/usr/share/batocera/launch/data/special \
		$(@D)/resources/data/special/*.toml

	$(INSTALL) -m 0755 -t $(TARGET_DIR)/usr/share/batocera/launch/scripts \
		$(@D)/resources/scripts/powermode_launch_hooks.sh

	# evmapy default hotkeys file
	$(INSTALL) -D -m 0644 -t $(TARGET_DIR)/usr/share/evmapy \
		$(@D)/resources/hotkeys.keys
endef

define BATOCERA_LAUNCH_INSTALL_X86_64_SCRIPTS
	mkdir -p $(TARGET_DIR)/usr/share/batocera/launch/scripts

	$(INSTALL) -m 0755 -t $(TARGET_DIR)/usr/share/batocera/launch/scripts \
		$(@D)/resources/scripts/tdp_hooks.sh \
		$(@D)/resources/scripts/nvidia-workaround.sh
endef

BATOCERA_LAUNCH_POST_INSTALL_TARGET_HOOKS += BATOCERA_LAUNCH_INSTALL_DEFAULT_OPTIONS
BATOCERA_LAUNCH_POST_INSTALL_TARGET_HOOKS += BATOCERA_LAUNCH_INSTALL_RESOURCES

ifeq ($(BR2_PACKAGE_BATOCERA_TARGET_X86_64_ANY),y)
BATOCERA_LAUNCH_POST_INSTALL_TARGET_HOOKS += BATOCERA_LAUNCH_INSTALL_X86_64_SCRIPTS
endif

BATOCERA_LAUNCH_POST_INSTALL_STAGING_HOOKS += BATOCERA_LAUNCH_INSTALL_STAGING_DEFAULT_OPTIONS

$(eval $(local-python-package))
