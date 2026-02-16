################################################################################
#
# toolchain-external-batocera-x86-64
#
################################################################################

TOOLCHAIN_EXTERNAL_BATOCERA_X86_64_VERSION = 2025.06
TOOLCHAIN_EXTERNAL_BATOCERA_X86_64_SITE = https://github.com/bryanforbes/batocera.linux/releases/download/sdk-$(TOOLCHAIN_EXTERNAL_BATOCERA_X86_64_VERSION)

ifneq ($(filter x86_64 aarch64,$(HOSTARCH)),)
TOOLCHAIN_EXTERNAL_BATOCERA_X86_64_SOURCE = batocera-sdk_x86_64-buildroot-linux-gnu_$(HOSTARCH).tar.gz
endif

$(eval $(toolchain-external-package))
