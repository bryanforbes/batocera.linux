# We want bash as shell
SHELL := $(shell if [ -x "$$BASH" ]; then echo $$BASH; \
	 else command -v bash 2>/dev/null; \
	 fi)

ifeq ($(SHELL),)
$(error Bash shell not found)
endif

# We want make 4.3+
ifneq ($(shell echo $$'4.3\n$(MAKE_VERSION)' | sort -V | head -n1),4.3)
$(error GNU Make 4.3 or higher is required, you are using $(MAKE_VERSION))
endif

# We don't use any of the default rules (including suffix rules),
# so disable them
MAKEFLAGS += --no-builtin-rules
.SUFFIXES:

OS := $(shell uname)

ifeq ($(OS),Darwin)
FIND ?= gfind
NPROC := $(shell sysctl -n hw.ncpu)
else
FIND ?= find
NPROC := $(shell nproc)
endif

PROJECT_DIR    := $(realpath $(CURDIR))
DL_DIR         ?= $(PROJECT_DIR)/dl
OUTPUT_DIR     ?= $(PROJECT_DIR)/output
CCACHE_DIR     ?= $(PROJECT_DIR)/buildroot-ccache
LOCAL_MK       ?= $(PROJECT_DIR)/batocera.mk
EXTRA_OPTS     ?=
DOCKER_OPTS    ?=
MAKE_JLEVEL    ?= $(NPROC)
MAKE_LLEVEL    ?= $(NPROC)
BATCH_MODE     ?=
PARALLEL_BUILD ?=
DIRECT_BUILD   ?=
DAYS           ?= 1
DOCKER         ?= docker
DOCKER_OPTS    ?=
DOCKER_REPO    ?= batoceralinux
DOCKER_IMAGE_NAME   ?= batocera.linux-build
SYSTEMS_REPORT_EXCLUDE_TARGETS ?= odin t527

USER_DEFCONFIG := $(PROJECT_DIR)/configs/.user_defconfig

define add-defconfig
$(file >>$(USER_DEFCONFIG),$(1))
endef

# Clear the user defconfig file at the start before including
# the user's makefile customizations
$(file >$(USER_DEFCONFIG),)

-include $(LOCAL_MK)

ifdef IMAGE_NAME
$(warning IMAGE_NAME will be removed in the future, please migrate to DOCKER_IMAGE_NAME)
DOCKER_IMAGE_NAME := $(IMAGE_NAME)
endif

DOCKER_IMAGE = $(DOCKER_REPO)/$(DOCKER_IMAGE_NAME)

ifdef EXTRA_OPTS
$(warning EXTRA_OPTS will be removed in the future, please migrate to $$(call add-defconfig,...))
$(foreach opt,$(EXTRA_OPTS),$(call add-defconfig,$(subst \",",$(opt))))
endif

ifndef BATCH_MODE
DOCKER_OPTS += -i
endif

ifdef PARALLEL_BUILD
$(call add-defconfig,BR2_PER_PACKAGE_DIRECTORIES=y)
$(call add-defconfig,BR2_JLEVEL=$(MAKE_JLEVEL))
MAKE_OPTS  += -j$(MAKE_JLEVEL)
MAKE_OPTS  += -l$(MAKE_LLEVEL)
endif

# List of packages that are always good to rebuild for versioning/stamps etc
MANDATORY_REBUILD_PKGS := batocera-es-system batocera-configgen batocera-system batocera-splash

# Lazily evaluated variable to avoid re-evaluation on each use
# VAR = $(eval VAR := ...)$(VAR)

# List of out-of-tree kernel modules that must be removed if the kernel is reset
# This list needs to be maintained if new modules are added or removed
KERNEL_MODULE_PKGS = $(eval KERNEL_MODULE_PKGS := $(sort $(patsubst %.mk,%,$(notdir $(shell grep -rl '\$$(eval \$$(kernel-module))' $(PROJECT_DIR)/package 2>/dev/null)))))$(KERNEL_MODULE_PKGS)

# Across all batocera & buildroot packages find any updates and add to a list to rebuild
GIT_PACKAGES_TO_REBUILD = $(eval GIT_PACKAGES_TO_REBUILD := $(shell \
	{ git -C $(PROJECT_DIR) log --since="$(DAYS) days ago" --name-only --format=%n -- package/ ; \
	  git -C $(PROJECT_DIR)/buildroot log --since="$(DAYS) days ago" --name-only --format=%n -- package/ ; } \
	| sed -r 's:^package/::; /^batocera\/[^/]*$$/d; s:^batocera/[^/]+/::; s:^([^/]+)/.*:\1:' \
	| sort -u))$(GIT_PACKAGES_TO_REBUILD)

# Base list of all target packages to be reset
TARGET_PKGS_BASE = $(GIT_PACKAGES_TO_REBUILD) $(MANDATORY_REBUILD_PKGS)

# Check if a kernel package is present and conditionally add 'linux' and kernel modules
KERNEL_MODULES_TO_RESET = $(if $(filter linux linux-headers,$(TARGET_PKGS_BASE)),linux $(KERNEL_MODULE_PKGS))

# Final list of all target packages to be reset (Base + Conditional Kernel Modules)
TARGET_PKGS = $(TARGET_PKGS_BASE) $(KERNEL_MODULES_TO_RESET)

# Cheats way, add 'host-' to each target package to ensure we are covered
HOST_PKGS_TO_RESET = $(addprefix host-,$(TARGET_PKGS))

# Final list is a combination of all target and host packages
PKGS_TO_RESET = $(sort $(TARGET_PKGS) $(HOST_PKGS_TO_RESET))

# All supported targets based on the board files in configs/, sorted for consistency
TARGETS := $(sort $(patsubst batocera-%.board,%,$(notdir $(wildcard $(PROJECT_DIR)/configs/*.board))))

# All supported targets for systems report generation
SYSTEMS_REPORT_TARGETS := $(filter-out $(SYSTEMS_REPORT_EXCLUDE_TARGETS) x86_wow64,$(TARGETS))

# All defconfig files for systems report targets, generated from the board files
SYSTEMS_REPORT_DEFCONFIGS = $(foreach target,$(SYSTEMS_REPORT_TARGETS),$(call TARGET_DEFCONFIG,$(target)))

## BEGIN helper macros

REQUIRE = $(if $(shell command -v $(1) 2>/dev/null),,$(error $(1) not found$(if $(2),; $(2))))
UC = $(shell echo '$1' | tr '[:lower:]' '[:upper:]')

TERM_BOLD := $(shell tput smso 2>/dev/null)
TERM_RESET := $(shell tput rmso 2>/dev/null)
TERM_URL = \e]8;;$(1)\e\\$(if $(2),$(2),$(1))\e]8;;\e\\
MESSAGE = printf '$(TERM_BOLD)>>> $*: %b$(TERM_RESET)\n' $$'$(call strip,$(subst ',\',$(1)))'

# END helper macros

.PHONY: vars
vars:
	@echo "Supported targets:  $(TARGETS)"
	@echo "Project directory:  $(PROJECT_DIR)"
	@echo "Download directory: $(DL_DIR)"
	@echo "Build directory:    $(OUTPUT_DIR)"
	@echo "ccache directory:   $(CCACHE_DIR)"
	@echo "Extra options:      $(EXTRA_OPTS)"
	@echo "Extra defconfig:"
	@sed -e '/^\s*$$/d' -e 's/^/  /' "$(USER_DEFCONFIG)"
ifndef DIRECT_BUILD
	@echo "Docker repo/image:  $(DOCKER_IMAGE)"
	@echo "Docker options:     $(DOCKER_OPTS)"
endif
	@echo "Make options:       $(MAKE_OPTS)"

## BEGIN docker rules and recipes

# define build command based on whether we are building direct or inside a docker build container
ifdef DIRECT_BUILD

define RUN_DOCKER
	@$(error This is a direct build environment, cannot run Docker)
endef

define MAKE_BUILDROOT
	make $(MAKE_OPTS) O=$(OUTPUT_DIR)/$* \
		BR2_EXTERNAL=$(PROJECT_DIR) \
		BR2_DL_DIR=$(DL_DIR) \
		BR2_CCACHE_DIR=$(CCACHE_DIR) \
		-C $(PROJECT_DIR)/buildroot
endef

else # DIRECT_BUILD

UID  := $(shell id -u)
GID  := $(shell id -g)

define RUN_DOCKER
	$(DOCKER) run -t --init --rm \
		-e HOME \
		-v $(PROJECT_DIR):/build \
		-v $(DL_DIR):/build/buildroot/dl \
		-v $(OUTPUT_DIR)/$*:/$* \
		-v $(CCACHE_DIR):$(HOME)/.buildroot-ccache \
		-w /$* \
		-v /etc/passwd:/etc/passwd:ro \
		-v /etc/group:/etc/group:ro \
		-u $(UID):$(GID) \
		$(DOCKER_OPTS) \
		$(DOCKER_IMAGE)
endef

define MAKE_BUILDROOT
	$(RUN_DOCKER) make $(MAKE_OPTS) O=/$* \
			BR2_EXTERNAL=/build \
			-C /build/buildroot
endef

endif # DIRECT_BUILD

.PHONY: _check_docker
_check_docker:
	$(if $(DIRECT_BUILD),$(error This is a direct build environment))
	$(call REQUIRE,$(DOCKER))

BA_DOCKER_IMAGE := $(if $(DIRECT_BUILD),,$(PROJECT_DIR)/.ba-docker-image-available)

$(PROJECT_DIR)/.ba-docker-image-available: DOCKER_ACTION ?= pull
$(PROJECT_DIR)/.ba-docker-image-available: | _check_docker
	$(if $(filter build,$(DOCKER_ACTION)),\
		$(DOCKER) build -t $(DOCKER_IMAGE) .,\
		$(DOCKER) pull $(DOCKER_IMAGE))
	@touch $@

.PHONY: pull-docker-image
pull-docker-image: DOCKER_ACTION = pull
pull-docker-image: $(BA_DOCKER_IMAGE)

.PHONY: build-docker-image
build-docker-image: DOCKER_ACTION = build
build-docker-image: $(BA_DOCKER_IMAGE)

.PHONY: clean-for-docker-image
clean-for-docker-image:
	-@rm -f .ba-docker-image-available >/dev/null

.PHONY: update-docker-image
update-docker-image: clean-for-docker-image
	@$(MAKE) pull-docker-image

.PHONY: rebuild-docker-image
rebuild-docker-image: clean-for-docker-image
	@$(MAKE) build-docker-image

.PHONY: publish-docker-image
publish-docker-image: | _check_docker
	@$(DOCKER) push $(DOCKER_IMAGE):latest

## END docker rules and recipes

.PHONY: _check_find
_check_find:
ifeq ($(OS),Darwin)
	$(call REQUIRE,gfind,Please install findutils from Homebrew)
endif

# Target macros for files or directories (actual files)
TARGET_OUTPUT_DIR = $(OUTPUT_DIR)/$(1)
TARGET_BOARD_FILE = $(PROJECT_DIR)/configs/batocera-$(1).board
TARGET_DEFCONFIG = $(PROJECT_DIR)/configs/batocera-$(1)_defconfig
TARGET_SYSTEMS_REPORT_DIR = $(OUTPUT_DIR)/$(1)/systems-report
TARGET_SYSTEMS_REPORT_MK = $(call TARGET_OUTPUT_DIR,$(1))/.systems_report_targets.mk

# Stamp files (used for sequencing)
CCACHE_DIR_INITIALIZED = $(CCACHE_DIR)/.stamp_initialized
DL_DIR_INITIALIZED = $(DL_DIR)/.stamp_initialized
TARGET_OUTPUT_DIR_INITIALIZED = $(call TARGET_OUTPUT_DIR,%)/.stamp_initialized

# Stamp pattern rules for initializing directories, ensuring they are
# only created once and can be used as dependencies for sequencing
.PRECIOUS: %/.stamp_initialized
%/.stamp_initialized:
	@mkdir -p $(@D)
	@touch $@

%-supported:
	$(if $(filter $*,$(TARGETS)),,$(error $* not supported))

%-clean: %-config
	@$(call MESSAGE,Cleaning build)
	@$(MAKE_BUILDROOT) clean
	@if [ -f $(PROJECT_DIR)/configs/batocera-$*_defconfig ]; then \
		echo "Removing config for $*..."; \
		rm $(PROJECT_DIR)/configs/batocera-$*_defconfig; \
	fi
	-@rm -f $(USER_DEFCONFIG)

%-defconfig: %-supported
	@$(PROJECT_DIR)/configs/createDefconfig.sh \
		$(call TARGET_BOARD_FILE,$*) \
		$(USER_DEFCONFIG) \
		$(call TARGET_DEFCONFIG,$*)

%-config: %-defconfig | $(BA_DOCKER_IMAGE) $(DL_DIR_INITIALIZED) $(CCACHE_DIR_INITIALIZED) $(TARGET_OUTPUT_DIR_INITIALIZED)
	@$(call MESSAGE,Generating Buildroot makefiles)
	@$(MAKE_BUILDROOT) batocera-$*_defconfig

%-build: BUILD_MESSAGE ?=
%-build: %-config
	@$(call MESSAGE,$(if $(BUILD_MESSAGE),$(BUILD_MESSAGE),Building$(if $(CMD), '$(CMD)',)))
	@$(MAKE_BUILDROOT) $(CMD)

%-source: %-config
	@$(call MESSAGE,Fetching source code for all packages)
	@$(MAKE_BUILDROOT) source

%-show-build-order: %-config
	@$(MAKE_BUILDROOT) show-build-order

%-kernel: %-config
	@$(MAKE_BUILDROOT) linux-menuconfig

# force -j1 or graph-depends python script will bail
%-graph-depends: %-config
	@$(MAKE_BUILDROOT) -j1 BR2_GRAPH_OUT=svg graph-depends

%-shell: %-config
ifdef BATCH_MODE
	$(if $(CMD),,$(error CMD is required to use $*-shell in BATCH_MODE))
endif
	@$(call MESSAGE,$(if $(CMD),Executing command,Starting interactive shell))
	@$(RUN_DOCKER) $(CMD)

%-ccache-stats: %-config
	@$(MAKE_BUILDROOT) ccache-stats

%-build-cmd: %-supported
	@echo $(MAKE_BUILDROOT)

%-clean-for-refresh: | $(TARGET_OUTPUT_DIR_INITIALIZED)
ifndef PARALLEL_BUILD
	$(error PARALLEL_BUILD=y must be set for $*-refresh)
endif
	@$(call MESSAGE,Refresh & Targeted Rebuild Trigger (DAYS=$(DAYS)))

	@if [ -n "$(PKGS_TO_RESET)" ]; then \
		echo "Total packages to reset: $(PKGS_TO_RESET)"; \
		for pkg in $(PKGS_TO_RESET); do \
			echo "Surgically removing $$pkg from build and per-package directories..."; \
			rm -rf $(OUTPUT_DIR)/$*/build/$$pkg-*; \
			rm -rf $(OUTPUT_DIR)/$*/per-package/$$pkg; \
		done; \
	else \
		echo "No packages to reset."; \
	fi

	@$(call MESSAGE,Removing Host and Target directories)
	@for dir in include share lib/pkgconfig; do \
		if [ -d "$(OUTPUT_DIR)/$*/host/$$dir" ]; then \
			echo "Cleaning host staging: $$dir..."; \
			rm -rf $(OUTPUT_DIR)/$*/host/$$dir; \
		fi; \
	done
	rm -rf $(OUTPUT_DIR)/$*/target
	rm -rf $(OUTPUT_DIR)/$*/target2

%-refresh: %-supported %-clean-for-refresh
	@$(MAKE) $*-build

%-cleanbuild: %-clean
	@$(MAKE) $*-build

%-pkg: %-supported
	$(if $(PKG),,$(error PKG not specified))

	@$(MAKE) $*-build CMD=$(PKG) BUILD_MESSAGE='Building package $(PKG)'

%-webserver: %-supported | $(TARGET_OUTPUT_DIR_INITIALIZED)
	$(if $(wildcard $(OUTPUT_DIR)/$*/images/batocera/*),,$(error $* not built!))
	$(call REQUIRE,python3)
ifeq ($(strip $(BOARD)),)
	$(if $(wildcard $(OUTPUT_DIR)/$*/images/batocera/images/$*),,$(error Directory not found: $(OUTPUT_DIR)/$*/images/batocera/images/$*))
	python3 -m http.server --directory $(OUTPUT_DIR)/$*/images/batocera/images/$*/
else
	$(if $(wildcard $(OUTPUT_DIR)/$*/images/batocera/images/$(BOARD)),,$(error Directory not found: $(OUTPUT_DIR)/$*/images/batocera/images/$(BOARD)))
	python3 -m http.server --directory $(OUTPUT_DIR)/$*/images/batocera/images/$(BOARD)/
endif

%-rsync: %-supported | $(TARGET_OUTPUT_DIR_INITIALIZED)
	$(eval TMP := $(call UC, $*)_IP)
	$(call REQUIRE,rsync)
	$(if $($(TMP)),,$(error "$(TMP) not set!"))
	rsync -e "ssh -o 'UserKnownHostsFile /dev/null' -o StrictHostKeyChecking=no" -av $(OUTPUT_DIR)/$*/target/ root@$($(TMP)):/

%-tail: %-supported
	@tail -F $(OUTPUT_DIR)/$*/build/build-time.log

%-snapshot: %-supported
	$(call REQUIRE,btrfs)
	@mkdir -p $(OUTPUT_DIR)/snapshots
	-@sudo btrfs sub del $(OUTPUT_DIR)/snapshots/$*-toolchain
	@btrfs subvolume snapshot -r $(OUTPUT_DIR)/$* $(OUTPUT_DIR)/snapshots/$*-toolchain

%-rollback: %-supported
	$(call REQUIRE,btrfs)
	-@sudo btrfs sub del $(OUTPUT_DIR)/$*
	@btrfs subvolume snapshot $(OUTPUT_DIR)/snapshots/$*-toolchain $(OUTPUT_DIR)/$*

%-flash: %-supported
	$(if $(DEV),,$(error "DEV not specified!"))
	@gzip -dc $(OUTPUT_DIR)/$*/images/batocera/images/$*/batocera-*.img.gz | sudo dd of=$(DEV) bs=5M status=progress
	@sync

%-upgrade: %-supported
	$(if $(DEV),,$(error "DEV not specified!"))
	-@sudo umount /tmp/mount
	-@mkdir -p /tmp/mount
	@sudo mount $(DEV)1 /tmp/mount
	@lsblk
	@ls /tmp/mount
	@echo "continue BATOCERA upgrade $(DEV)1 with $* build? [y/N]"
	@read line; if [ "$$line" != "y" ]; then echo aborting; exit 1 ; fi
	-@sudo rm /tmp/mount/boot/batocera
	@sudo tar xvf $(OUTPUT_DIR)/$*/images/batocera/images/$*/boot.tar.xz -C /tmp/mount --no-same-owner --exclude=batocera-boot.conf --exclude=config.txt
	@sudo umount /tmp/mount
	-@rmdir /tmp/mount
	@sudo fatlabel $(DEV)1 BATOCERA

%-toolchain: %-supported
	$(call REQUIRE,btrfs)
	-@sudo btrfs sub del $(OUTPUT_DIR)/$*
	@btrfs subvolume create $(OUTPUT_DIR)/$*
	@$(MAKE) $*-config
	@$(MAKE) $*-build CMD=toolchain
	@$(MAKE) $*-build CMD=llvm
	@$(MAKE) $*-snapshot

%-find-build-dups: %-supported _check_find
	@$(FIND) $(OUTPUT_DIR)/$*/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -E 's:\-[0-9a-f\.]+$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2

%-remove-build-dups: %-supported _check_find
	@while [ -n "`$(FIND) $(OUTPUT_DIR)/$*/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -r 's:\-[0-9a-f\.]+$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2 | grep .`" ]; do \
		$(FIND) $(OUTPUT_DIR)/$*/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -r 's:\-[0-9a-f\.]+$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2 | xargs rm -rf ; \
	done

.PHONY: find-dl-dups
find-dl-dups: _check_find
	@$(FIND) $(DL_DIR)/ -maxdepth 2 -type f -name "*.zip" -o -name "*.tar.*" -printf '%T@ %p %f\n' | sed -r 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2

.PHONY: remove-dl-dups
remove-dl-dups: _check_find
	@while [ -n "`$(FIND) $(DL_DIR)/ -maxdepth 2 -type f -name "*.zip" -o -name "*.tar.*" -printf '%T@ %p %f\n' | sed -r 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2 | grep .`" ] ; do \
		$(FIND) $(DL_DIR) -maxdepth 2 -type f -name "*.zip" -o -name "*.tar.*" -printf '%T@ %p %f\n' | sed -r 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2 | xargs rm -rf ; \
	done

.PHONY: uart
uart:
	$(call REQUIRE,picocom)
	$(if $(SERIAL_DEV),,$(error "SERIAL_DEV not specified!"))
	$(if $(SERIAL_BAUDRATE),,$(error "SERIAL_BAUDRATE not specified!"))
	$(if $(wildcard $(SERIAL_DEV)),,$(error "$(SERIAL_DEV) not available!"))
	@picocom $(SERIAL_DEV) -b $(SERIAL_BAUDRATE)

%-update-po-files: %-config
	@$(call MESSAGE,Updating repository .po files)
	@$(MAKE_BUILDROOT) update-po-files

%-systems-report-clean: %-supported
	-@rm -rf $(call TARGET_SYSTEMS_REPORT_DIR,$*)

%-systems-report: $(SYSTEMS_REPORT_DEFCONFIGS) %-config
	@$(file >$(call TARGET_SYSTEMS_REPORT_MK,$*),SYSTEMS_REPORT_TARGETS := $(SYSTEMS_REPORT_TARGETS))
	@$(call MESSAGE,Generating systems report)
	@$(MAKE_BUILDROOT) systems-report

%-systems-report-serve: %-supported
	$(call REQUIRE,python3)
	@if [ ! -f $(call TARGET_SYSTEMS_REPORT_DIR,$*)/batocera_systemsReport.json ]; then \
		$(MAKE) $*-systems-report-build; \
	fi
	@$(call MESSAGE,Serving systems report at $(call TERM_URL,http://localhost:8000/batocera_systemsReport.html))
	python3 -m http.server --directory $(call TARGET_SYSTEMS_REPORT_DIR,$*)/
