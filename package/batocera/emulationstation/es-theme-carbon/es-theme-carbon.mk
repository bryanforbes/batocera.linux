################################################################################
#
# es-theme-carbon
#
################################################################################
# Version: Commits on Apr 5, 2025
ES_THEME_CARBON_VERSION = 40a737b891d172e786d7a8dc3837ac314ec77bef
ES_THEME_CARBON_SITE = $(call github,fabricecaruso,es-theme-carbon,$(ES_THEME_CARBON_VERSION))

define ES_THEME_CARBON_INSTALL_TARGET_CMDS
    mkdir -p $(TARGET_DIR)/usr/share/emulationstation/themes/es-theme-carbon
    cp -r $(@D)/* $(TARGET_DIR)/usr/share/emulationstation/themes/es-theme-carbon
endef

$(eval $(generic-package))
