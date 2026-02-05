OS := $(shell uname)

ifeq ($(OS),Darwin)
FIND  ?= gfind
NPROC := $(shell sysctl -n hw.ncpu)
else
FIND  ?= find
NPROC := $(shell nproc)
endif

PROJECT_DIR    := $(CURDIR)
DL_DIR         ?= $(PROJECT_DIR)/dl
OUTPUT_DIR     ?= $(PROJECT_DIR)/output
CCACHE_DIR     ?= $(PROJECT_DIR)/buildroot-ccache
LOCAL_MK       ?= $(PROJECT_DIR)/batocera.mk
EXTRA_OPTS     ?=
MAKE_JLEVEL    ?= $(NPROC)
MAKE_LLEVEL    ?= $(NPROC)
BATCH_MODE     ?=
PARALLEL_BUILD ?=
DIRECT_BUILD   ?=
DAYS           ?= 1
DOCKER         ?= docker
DOCKER_OPTS    ?=
DOCKER_REPO    ?= batoceralinux
DOCKER_IMAGE   ?= batocera.linux-build
SYSTEMS_REPORT_EXCLUDE_TARGETS ?= odin t527

-include $(LOCAL_MK)

ifndef BATCH_MODE
	DOCKER_OPTS += -i
endif

ifdef PARALLEL_BUILD
	EXTRA_OPTS +=  BR2_PER_PACKAGE_DIRECTORIES=y
	MAKE_OPTS  += -j$(MAKE_JLEVEL)
	MAKE_OPTS  += -l$(MAKE_LLEVEL)
endif

## HELPER MACROS

# Changes a lazily-evaluated variable (that will run its expression every time it is expaneded)
# into a lazily-evaluated variable that only runs its expression once. The variable is
# transformed into the following:
# VAR = $(eval VAR := <expensive expression>)$(VAR)
define lazy-cache
$(eval $(1)=$$(eval $(1):=$(value $(1)))$$($(1)))
endef

define __done-for-target
.PHONY: __$(1)-done
__$(1)-done: $(1)
endef

define done-for-target
$(eval $(call __done-for-target,$(1)))
endef

REQUIRE = $(if $(shell command -v $(1) 2>/dev/null),,$(error $(1) not found$(if $(2),; $(2))))
UC = $(shell echo '$(1)' | tr '[:lower:]-' '[:upper:]_')

## END HELPER MACROS

# List of packages that are always good to rebuild for versioning/stamps etc
MANDATORY_REBUILD_PKGS := batocera-es-system batocera-configgen batocera-system batocera-splash

# List of out-of-tree kernel modules that must be removed if the kernel is reset
# This list needs to be maintained if new modules are added or removed
KERNEL_MODULE_PKGS = $(sort $(patsubst %.mk,%,$(notdir $(shell grep -rl '\$$(eval \$$(kernel-module))' $(PROJECT_DIR)/package 2>/dev/null))))
$(call lazy-cache,KERNEL_MODULE_PKGS)

# Across all batocera & buildroot packages find any updates and add to a list to rebuild
GIT_PACKAGES_TO_REBUILD = $(shell \
	{ git -C $(PROJECT_DIR) log --since="$(DAYS) days ago" --name-only --format=%n -- package/ ; \
	  git -C $(PROJECT_DIR)/buildroot log --since="$(DAYS) days ago" --name-only --format=%n -- package/ ; } \
	| sed -E 's:^package/::; /^batocera\/[^/]*$$/d; s:^batocera/[^/]+/::; s:^([^/]+)/.*:\1:' \
	| sort -u)
$(call lazy-cache,GIT_PACKAGES_TO_REBUILD)

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

TARGETS := $(sort $(patsubst batocera-%.board,%,$(notdir $(wildcard $(PROJECT_DIR)/configs/*.board))))

UID  := $(shell id -u)
GID  := $(shell id -g)

.PHONY: vars
vars:
	@echo "Supported targets:  $(TARGETS)"
	@echo "Project directory:  $(PROJECT_DIR)"
	@echo "Download directory: $(DL_DIR)"
	@echo "Build directory:    $(OUTPUT_DIR)"
	@echo "ccache directory:   $(CCACHE_DIR)"
	@echo "Extra options:      $(EXTRA_OPTS)"
ifndef DIRECT_BUILD
	@echo "Docker repo/image:  $(DOCKER_REPO)/$(DOCKER_IMAGE)"
	@echo "Docker options:     $(DOCKER_OPTS)"
endif
	@echo "Make options:       $(MAKE_OPTS)"

.PHONY: _check_docker
_check_docker:
	$(if $(DIRECT_BUILD),$(error "This is a direct build environment"))
	$(call REQUIRE,$(DOCKER))

.PHONY: _check_find
_check_find:
ifeq ($(OS),Darwin)
	$(call REQUIRE,gfind,Please install findutils from Homebrew)
endif

BA_DOCKER_IMAGE := $(if $(DIRECT_BUILD),,.ba-docker-image-available)

.ba-docker-image-available: DOCKER_ACTION ?= pull
.ba-docker-image-available: | _check_docker
	$(if $(filter build,$(DOCKER_ACTION)),\
		$(DOCKER) build -t $(DOCKER_REPO)/$(DOCKER_IMAGE) .,\
		$(DOCKER) pull $(DOCKER_REPO)/$(DOCKER_IMAGE))
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

$(call done-for-target,clean-for-docker-image)

.PHONY: update-docker-image
update-docker-image: clean-for-docker-image
	@$(MAKE) pull-docker-image

.PHONY: rebuild-docker-image
rebuild-docker-image: clean-for-docker-image
	@$(MAKE) build-docker-image

.PHONY: publish-docker-image
publish-docker-image: | _check_docker
	@$(DOCKER) push $(DOCKER_REPO)/$(DOCKER_IMAGE):latest

# This rule causes targets that depend on it to always run
.PHONY: FORCE
FORCE:

# This is needed so that when SYSTEMS_REPORT_TARGETS_DEFCONFIGS is referenced
# by <TARGET>_TARGET_SYSTEMS_REPORT it gets expanded at the time of the rule execution
# rather than when the rule is defined.
.SECONDEXPANSION:

SYSTEMS_REPORT_TARGETS := $(filter-out $(SYSTEMS_REPORT_EXCLUDE_TARGETS) x86_wow64,$(TARGETS))

CCACHE_DIR_INITIALIZED := $(CCACHE_DIR)/.stamp_initialized
DL_DIR_INITIALIZED     := $(DL_DIR)/.stamp_initialized

# Ensure required directories are initialized
.PRECIOUS: %/.stamp_initialized
%/.stamp_initialized:
	@mkdir -p $(@D)
	@touch $@

$(OUTPUT_DIR)/%/.stamp_extra_opts:
	@# NOTE: these MUST be single quotes to avoid shell expansion of variables
	@# Write EXTRA_OPTS to a temp file, compare with existing, and only move if changed
	@echo '$(EXTRA_OPTS)' > $@.tmp
	@cmp -s $@.tmp $@ 2>/dev/null || mv -f $@.tmp $@
	@rm -f $@.tmp

# Generates target defconfig if it does not exist or is out-of-date
$(PROJECT_DIR)/configs/batocera-%_defconfig:
	@$(PROJECT_DIR)/configs/createDefconfig.sh $(BOARD_FILE) $@.tmp
	@for opt in $(EXTRA_OPTS); do \
		echo "$${opt}" >> $@.tmp ; \
	done
	@cmp -s $@.tmp $@ 2>/dev/null || mv -f $@.tmp $@
	@rm -f $@.tmp

$(OUTPUT_DIR)/%/.config:
	@$(TARGET_MAKE_BUILDROOT) batocera-$*_defconfig

$(OUTPUT_DIR)/%/.systems_report_targets.mk:
	@echo "SYSTEMS_REPORT_TARGETS := $(SYSTEMS_REPORT_TARGETS)" > $@

$(OUTPUT_DIR)/%/systems-report/batocera_systemsReport.json:
	$(TARGET_MAKE_BUILDROOT) systems-report

define target-rules
$(2)_OUTPUT_DIR = $$(OUTPUT_DIR)/$(1)
$(2)_SYSTEMS_REPORT_DIR = $$($(2)_OUTPUT_DIR)/systems-report

# Stamp files and artifacts
$(2)_TARGET_OUTPUT_DIR = $$($(2)_OUTPUT_DIR)/.stamp_initialized
$(2)_TARGET_EXTRA_OPTS = $$($(2)_OUTPUT_DIR)/.stamp_extra_opts
$(2)_TARGET_DEFCONFIG = $$(PROJECT_DIR)/configs/batocera-$(1)_defconfig
$(2)_TARGET_CONFIG = $$($(2)_OUTPUT_DIR)/.config
$(2)_TARGET_SYSTEMS_REPORT_MK = $$($(2)_OUTPUT_DIR)/.systems_report_targets.mk
$(2)_TARGET_SYSTEMS_REPORT = $$($(2)_SYSTEMS_REPORT_DIR)/batocera_systemsReport.json

$(2)_BR_DIRS = $$(CCACHE_DIR_INITIALIZED) $$(DL_DIR_INITIALIZED) $$($(2)_TARGET_OUTPUT_DIR)

ifdef DIRECT_BUILD
$(2)_RUN_DOCKER = $$(error This is a direct build environment)

$(2)_MAKE_BUILDROOT = make $$(MAKE_OPTS) O=$$($(2)_OUTPUT_DIR) \
			BR2_EXTERNAL=$$(PROJECT_DIR) \
			BR2_DL_DIR=$$(DL_DIR) \
			BR2_CCACHE_DIR=$$(CCACHE_DIR) \
			-C $$(PROJECT_DIR)/buildroot
else
$(2)_RUN_DOCKER = $$(DOCKER) run -t --init --rm \
			-e HOME \
			-v $$(PROJECT_DIR):/build \
			-v $$(DL_DIR):/build/buildroot/dl \
			-v $$($(2)_OUTPUT_DIR):/$(1) \
			-v $$(CCACHE_DIR):$$(HOME)/.buildroot-ccache \
			-w /$(1) \
			-v /etc/passwd:/etc/passwd:ro \
			-v /etc/group:/etc/group:ro \
			-u $$(UID):$$(GID) \
			$$(DOCKER_OPTS) \
			$$(DOCKER_REPO)/$$(DOCKER_IMAGE)

$(2)_MAKE_BUILDROOT = $$($(2)_RUN_DOCKER) \
			make $$(MAKE_OPTS) O=/$(1) \
				BR2_EXTERNAL=/build \
				-C /build/buildroot
endif # DIRECT_BUILD

# human friendly rules and target sequencing
#
$$($(2)_TARGET_EXTRA_OPTS): FORCE
$$($(2)_TARGET_EXTRA_OPTS): | $$($(2)_TARGET_OUTPUT_DIR)

$(1)-defconfig: $$($(2)_TARGET_DEFCONFIG)
$$($(2)_TARGET_DEFCONFIG): $$(PROJECT_DIR)/configs/batocera-$(1).board
$$($(2)_TARGET_DEFCONFIG): $$(PROJECT_DIR)/configs/batocera-board.common
$$($(2)_TARGET_DEFCONFIG): $$($(2)_TARGET_EXTRA_OPTS)

$(1)-config: $$($(2)_TARGET_CONFIG)
$$($(2)_TARGET_CONFIG): $$($(2)_TARGET_DEFCONFIG)
$$($(2)_TARGET_CONFIG): | $$(BA_DOCKER_IMAGE) $$($(2)_BR_DIRS)

$(1)-clean:
	@$$($(2)_MAKE_BUILDROOT) clean
$(1)-clean: $$($(2)_TARGET_CONFIG)

$$(call done-for-target,$(1)-clean)

$(1)-build:
	@$$($(2)_MAKE_BUILDROOT) $$(CMD)
$(1)-build: $$($(2)_TARGET_CONFIG)

$(1)-source:
	@$$($(2)_MAKE_BUILDROOT) source
$(1)-source: $$($(2)_TARGET_CONFIG)

$(1)-show-build-order:
	@$$($(2)_MAKE_BUILDROOT) show-build-order
$(1)-show-build-order: $$($(2)_TARGET_CONFIG)

$(1)-kernel:
	@$$($(2)_MAKE_BUILDROOT) linux-menuconfig
$(1)-kernel: $$($(2)_TARGET_CONFIG)

# force -j1 or graph-depends python script will bail
$(1)-graph-depends:
	@$$($(2)_MAKE_BUILDROOT) -j1 BR2_GRAPH_OUT=svg graph-depends
$(1)-graph-depends: $$($(2)_TARGET_CONFIG)

ifdef BATCH_MODE
$(1)-shell:
	$$(if $$(CMD),,$$(error not supported in BATCH_MODE if CMD not specified!))
endif

$(1)-shell:
	@$$($(2)_RUN_DOCKER) $$(CMD)
$(1)-shell: $$($(2)_TARGET_DEFCONFIG)
$(1)-shell: | $$(BA_DOCKER_IMAGE)
$(1)-shell: | $$($(2)_TARGET_OUTPUT_DIR)

$(1)-ccache-stats:
	@$$($(2)_MAKE_BUILDROOT) ccache-stats
$(1)-ccache-stats: | $$($(2)_TARGET_CONFIG)

$(1)-build-cmd:
	@echo $$($(2)_MAKE_BUILDROOT)

$(1)-clean-for-refresh:
ifndef PARALLEL_BUILD
	$$(error PARALLEL_BUILD=y must be set for $(1)-refresh)
else
	@echo "--- Refresh & Targeted Rebuild Trigger (DAYS=$$(DAYS)) ---"

	@if [ -n "$$(PKGS_TO_RESET)" ]; then \
		echo "Total packages to reset: $$(PKGS_TO_RESET)"; \
		for pkg in $$(PKGS_TO_RESET); do \
			echo "Surgically removing $$$${pkg} from build and per-package directories..."; \
			rm -rf $$($(2)_OUTPUT_DIR)/build/$$$${pkg}-*; \
			rm -rf $$($(2)_OUTPUT_DIR)/per-package/$$$${pkg}; \
		done; \
	else \
		echo "No packages to reset."; \
	fi

	@echo "--- Removing Host and Target directories ---"
	rm -rf $$($(2)_OUTPUT_DIR)/host
	rm -rf $$($(2)_OUTPUT_DIR)/target
	rm -rf $$($(2)_OUTPUT_DIR)/target2
endif
$(1)-clean-for-refresh: | $$($(2)_TARGET_OUTPUT_DIR)
$$(call done-for-target,$(1)-clean-for-refresh)

$(1)-refresh: $(1)-clean-for-refresh __$(1)-clean-for-refresh-done $(1)-build

$(1)-cleanbuild: $(1)-clean __$(1)-clean-done $(1)-build

$(1)-pkg:
	$$(if $$(PKG),,$$(error PKG not specified!))

	@$$(MAKE) $(1)-build CMD=$$(PKG)

$(1)-webserver: | $$($(2)_TARGET_OUTPUT_DIR)
	$$(if $$(wildcard $$($(2)_OUTPUT_DIR)/images/batocera/*),,$$(error $(1) not built!))
	$$(call REQUIRE,python3)
ifeq ($$(strip $$(BOARD)),)
	@test -d "$$($(2)_OUTPUT_DIR)/images/batocera/images/$(1)" || { echo "Directory not found: $$($(2)_OUTPUT_DIR)/images/batocera/images/$(1)"; exit 1; }
	python3 -m http.server --directory $$($(2)_OUTPUT_DIR)/images/batocera/images/$(1)/
else
	@test -d "$$($(2)_OUTPUT_DIR)/images/batocera/images/$$(BOARD)" || { echo "Directory not found: $$($(2)_OUTPUT_DIR)/images/batocera/images/$$(BOARD)"; exit 1; }
	python3 -m http.server --directory $$($(2)_OUTPUT_DIR)/images/batocera/images/$$(BOARD)/
endif

$(1)-rsync:
	$$(eval TMP := $(2)_IP)
	$$(call REQUIRE,rsync)
	$$(if $$($$(TMP)),,$$(error "$$(TMP) not set!"))
	rsync -e "ssh -o 'UserKnownHostsFile /dev/null' -o StrictHostKeyChecking=no" -av $$($(2)_OUTPUT_DIR)/target/ root@$$($$(TMP)):/
$(1)-rsync: | $$($(2)_TARGET_OUTPUT_DIR)

$(1)-tail:
	@tail -F $$($(2)_OUTPUT_DIR)/build/build-time.log

$(1)-snapshot:
	$$(call REQUIRE,btrfs)
	@mkdir -p $$(OUTPUT_DIR)/snapshots
	-@sudo btrfs sub del $$(OUTPUT_DIR)/snapshots/$(1)-toolchain
	@btrfs subvolume snapshot -r $$($(2)_OUTPUT_DIR) $$(OUTPUT_DIR)/snapshots/$(1)-toolchain

$(1)-rollback:
	$$(call REQUIRE,btrfs)
	-@sudo btrfs sub del $$($(2)_OUTPUT_DIR)
	@btrfs subvolume snapshot $$(OUTPUT_DIR)/snapshots/$(1)-toolchain $$($(2)_OUTPUT_DIR)

$(1)-flash:
	$$(if $$(DEV),,$$(error "DEV not specified!"))
	@gzip -dc $$($(2)_OUTPUT_DIR)/images/batocera/images/$(1)/batocera-*.img.gz | sudo dd of=$$(DEV) bs=5M status=progress
	@sync

$(1)-upgrade:
	$$(if $$(DEV),,$$(error "DEV not specified!"))
	-@sudo umount /tmp/mount
	-@mkdir -p /tmp/mount
	@sudo mount $$(DEV)1 /tmp/mount
	@lsblk
	@ls /tmp/mount
	@echo "continue BATOCERA upgrade $$(DEV)1 with $(1) build? [y/N]"
	@read line; if [ "$$$$line" != "y" ]; then echo aborting; exit 1 ; fi
	-@sudo rm /tmp/mount/boot/batocera
	@sudo tar xvf $$($(2)_OUTPUT_DIR)/images/batocera/images/$(1)/boot.tar.xz -C /tmp/mount --no-same-owner --exclude=batocera-boot.conf --exclude=config.txt
	@sudo umount /tmp/mount
	-@rmdir /tmp/mount
	@sudo fatlabel $$(DEV)1 BATOCERA

$(1)-toolchain:
	$$(call REQUIRE,btrfs)
	-@sudo btrfs sub del $$($(2)_OUTPUT_DIR)
	@btrfs subvolume create $$($(2)_OUTPUT_DIR)
	@$$(MAKE) $(1)-config
	@$$(MAKE) $(1)-build CMD=toolchain
	@$$(MAKE) $(1)-build CMD=llvm
	@$$(MAKE) $(1)-snapshot

$(1)-find-build-dups:
	@$$(FIND) $$($(2)_OUTPUT_DIR)/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -E 's:\-[0-9a-f\.]+$$$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2
$(1)-find-build-dups: _check_find

$(1)-remove-build-dups:
	@dups="$$$$($$(FIND) $$($(2)_OUTPUT_DIR)/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -E 's:\-[0-9a-f\.]+$$$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2)"; \
	while [ -n "$$$$dups" ]; do \
		echo "$$$$dups" | xargs -r rm -rf; \
		dups="$$$$($$(FIND) $$($(2)_OUTPUT_DIR)/build -maxdepth 1 -type d -printf '%T@ %p %f\n' | sed -E 's:\-[0-9a-f\.]+$$$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2)"; \
	done
$(1)-remove-build-dups: _check_find

$(1)-update-po-files:
	@$$(MAKE_BUILDROOT) update-po-files
$(1)-update-po-files: $$($(2)_TARGET_CONFIG)

.INTERMEDIATE: $$($(2)_TARGET_SYSTEMS_REPORT_MK)
$$($(2)_TARGET_SYSTEMS_REPORT_MK): | $$($(2)_TARGET_OUTPUT_DIR)

$(1)-systems-report-build: $$($(2)_TARGET_SYSTEMS_REPORT)
$$($(2)_TARGET_SYSTEMS_REPORT): $$$$(SYSTEMS_REPORT_TARGETS_DEFCONFIGS)
$$($(2)_TARGET_SYSTEMS_REPORT): $$($(2)_TARGET_CONFIG)
$$($(2)_TARGET_SYSTEMS_REPORT): | $$($(2)_TARGET_SYSTEMS_REPORT_MK)

$(1)-systems-report-clean:
	-@rm -rf $$($(2)_OUTPUT_DIR)/systems-report

$$(call done-for-target,$(1)-systems-report-clean)

$(1)-systems-report: $(1)-systems-report-clean __$(1)-systems-report-clean-done $(1)-systems-report-build

$(1)-systems-report-serve: | $$($(2)_TARGET_SYSTEMS_REPORT)
	$$(call REQUIRE,python3)
	python3 -m http.server --directory $$($(2)_OUTPUT_DIR)/systems-report/

# define the variables for targets
$$($(2)_TARGET_DEFCONFIG):      BOARD_FILE=$$(PROJECT_DIR)/configs/batocera-$(1).board
$$($(2)_TARGET_CONFIG):         TARGET_MAKE_BUILDROOT=$$($(2)_MAKE_BUILDROOT)
$$($(2)_TARGET_SYSTEMS_REPORT): TARGET_MAKE_BUILDROOT=$$($(2)_MAKE_BUILDROOT)
# Run the systems report in parallel
$$($(2)_TARGET_SYSTEMS_REPORT): MAKE_OPTS=-j$(MAKE_JLEVEL) -l$(MAKE_LLEVEL) BR2_PER_PACKAGE_DIRECTORIES=y

ifeq ($(filter $(1),$(SYSTEMS_REPORT_TARGETS)),$(1))
SYSTEMS_REPORT_TARGETS_DEFCONFIGS += $$($(2)_TARGET_DEFCONFIG)
endif

# Ensure all virtual targets are PHONY.
.PHONY: $(1)-defconfig \
	$(1)-config \
	$(1)-clean \
	$(1)-build \
	$(1)-source \
	$(1)-show-build-order \
	$(1)-kernel \
	$(1)-graph-depends \
	$(1)-shell \
	$(1)-ccache-stats \
	$(1)-build-cmd \
	$(1)-clean-for-refresh \
	$(1)-refresh \
	$(1)-cleanbuild \
	$(1)-pkg \
	$(1)-webserver \
	$(1)-rsync \
	$(1)-tail \
	$(1)-snapshot \
	$(1)-rollback \
	$(1)-flash \
	$(1)-upgrade \
	$(1)-toolchain \
	$(1)-find-build-dups \
	$(1)-remove-build-dups \
	$(1)-update-po-files \
	$(1)-systems-report \
	$(1)-systems-report-build \
	$(1)-systems-report-clean \
	$(1)-systems-report-serve
endef

$(foreach target,$(TARGETS),$(eval $(call target-rules,$(target),$(call UC,$(target)))))

.PHONY: find-dl-dups
find-dl-dups: | _check_find
	@$(FIND) $(DL_DIR)/ -maxdepth 2 -type f \( -name "*.zip" -o -name "*.tar.*" \) -printf '%T@ %p %f\n' | sed -E 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2

.PHONY: remove-dl-dups
remove-dl-dups: | _check_find
	@dups="$$($(FIND) $(DL_DIR)/ -maxdepth 2 -type f \( -name "*.zip" -o -name "*.tar.*" \) -printf '%T@ %p %f\n' | sed -E 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2)"; \
	while [ -n "$$dups" ]; do \
		echo "$$dups" | xargs -r rm -rf; \
		dups="$$($(FIND) $(DL_DIR)/ -maxdepth 2 -type f \( -name "*.zip" -o -name "*.tar.*" \) -printf '%T@ %p %f\n' | sed -E 's:\-[-_0-9a-fvrgit\.]+(\.zip|\.tar\.[2a-z]+)$$::' | sort -k3 -k1 | uniq -f 2 -d | cut -d' ' -f2)"; \
	done

.PHONY: uart
uart:
	$(call REQUIRE,picocom)
	$(if $(SERIAL_DEV),,$(error "SERIAL_DEV not specified!"))
	$(if $(SERIAL_BAUDRATE),,$(error "SERIAL_BAUDRATE not specified!"))
	$(if $(wildcard $(SERIAL_DEV)),,$(error "$(SERIAL_DEV) not available!"))
	@picocom $(SERIAL_DEV) -b $(SERIAL_BAUDRATE)
