FROM ubuntu:22.04
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive

RUN <<EOF
# device-tree-compiler: required for device-trees-aml-s9xx
# gettext: required for buildstats.sh
PACKAGES=(
	"build-essential"
	"cmake"
	"git"
	"libncurses6"
	"libncurses-dev"
	"libssl-dev"
	"mercurial"
	"texinfo"
	"zip"
	"default-jre"
	"imagemagick"
	"subversion"
	"autoconf"
	"automake"
	"bison"
	"scons"
	"libglib2.0-dev"
	"bc"
	"mtools"
	"u-boot-tools"
	"flex"
	"wget"
	"cpio"
	"dosfstools"
	"libtool"
	"rsync"
	"device-tree-compiler"
	"gettext"
	"locales"
	"graphviz"
	"python3"
)

apt-get update
apt-get install -y -o APT::Immediate-Configure=0 "${PACKAGES[@]}"
apt-get clean
rm -rf /var/lib/apt/lists/*

# Set locale
sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen
locale-gen

mkdir -p /build
EOF

# Set locale
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US:en
ENV LC_ALL=en_US.UTF-8
ENV TZ=Europe/Paris

# Workaround host-tar configure error
ENV FORCE_UNSAFE_CONFIGURE=1

WORKDIR /build
CMD ["/bin/bash"]
