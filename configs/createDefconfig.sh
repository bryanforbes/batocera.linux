#!/bin/sh

BOARD_FILE="$1"
DEFCONFIG_FILE="$2"

if ! test -e "${BOARD_FILE}"
then
    echo "file ${BOARD_FILE} not found" >&2
    exit 1
fi

CONFIG_DIR="$(dirname ${BOARD_FILE})"

TMPL0="${DEFCONFIG_FILE}.tmpl0"
TMPL1="${DEFCONFIG_FILE}.tmpl1"

> "${TMPL0}" || exit 1 # level 0
> "${TMPL1}" || exit 1 # level 1 (includes of includes)

grep -E 'include ' "${BOARD_FILE}" | while read INC X
do
    if [ -f "${CONFIG_DIR}/${X}" ]; then
        echo "# from file ${X}" >> "${TMPL0}"
        cat "${CONFIG_DIR}/${X}"   >> "${TMPL0}"
        echo                    >> "${TMPL0}"
    fi
done

grep -E 'include ' "${TMPL0}" | while read INC X
do
    if [ -f "${CONFIG_DIR}/${X}" ]; then
        echo "# from file ${X}" >> "${TMPL1}"
        cat "${CONFIG_DIR}/${X}"   >> "${TMPL1}"
        echo                    >> "${TMPL1}"
    fi
done

> "${DEFCONFIG_FILE}" || exit 1
grep -vE '^include ' "${TMPL1}" >> "${DEFCONFIG_FILE}"
grep -vE '^include ' "${TMPL0}" >> "${DEFCONFIG_FILE}"

rm -f "${TMPL1}" || exit 1
rm -f "${TMPL0}" || exit 1

echo "### from board file ###"   >> "${DEFCONFIG_FILE}" || exit 1
grep -vE '^include ' "${BOARD_FILE}" >> "${DEFCONFIG_FILE}" || exit 1

exit 0
