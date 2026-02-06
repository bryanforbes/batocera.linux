#!/bin/bash

BOARD_FILE="$1"
EXTRA_OPTS_FILE="$2"
DEFCONFIG_FILE="$3"

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

# Include only if the file exists:
# -include something.local

# Include always:
# include something.local

include-file() {
    local INCLUDED_FILE="${1}"
    local OUTFILE="${2}"

    echo "# from file ${INCLUDED_FILE}"  >> "${OUTFILE}"
    cat "${CONFIG_DIR}/${INCLUDED_FILE}" >> "${OUTFILE}"
    echo                                 >> "${OUTFILE}"
}

parse-includes() {
    local INFILE="${1}"
    local OUTFILE="${2}"

    while read INC X; do
        if [ "${INC#-}" = "$INC" ] && [ ! -f "${CONFIG_DIR}/${X}" ]; then
            echo "Error: included file ${X} not found (included from ${INFILE})" >&2
            exit 1
        fi

        if [ -f "${CONFIG_DIR}/${X}" ]; then
            include-file "${X}" "${OUTFILE}"
        fi
    done < <(grep -E '^-?include ' "${INFILE}")
}

parse-includes "${BOARD_FILE}" "${TMPL0}"
parse-includes "${TMPL0}" "${TMPL1}"

> "${DEFCONFIG_FILE}" || exit 1
grep -vE '^-?include ' "${TMPL1}" >> "${DEFCONFIG_FILE}"
grep -vE '^-?include ' "${TMPL0}" >> "${DEFCONFIG_FILE}"

rm -f "${TMPL1}" || exit 1
rm -f "${TMPL0}" || exit 1

echo "### from board file ###"   >> "${DEFCONFIG_FILE}" || exit 1
grep -vE '^-?include ' "${BOARD_FILE}" >> "${DEFCONFIG_FILE}" || exit 1

echo "### from add-extra-opt ###"  >> "${DEFCONFIG_FILE}" || exit 1
grep -vE '^-?include ' "${EXTRA_OPTS_FILE}" >> "${DEFCONFIG_FILE}" || exit 1

exit 0
