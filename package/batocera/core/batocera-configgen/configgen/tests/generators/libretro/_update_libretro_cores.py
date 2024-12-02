#!/usr/bin/env python
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypedDict, cast

from ruamel.yaml import YAML

if TYPE_CHECKING:
    from collections.abc import Iterable

_PARENT_DIR: Final = Path(__file__).parent
_CORES_TEMPLATE: Final = """# This file was generated using _update_libretro_systems.py
from __future__ import annotations

from typing import Final, TypedDict
from typing_extensions import ReadOnly


class CoreDict(TypedDict):
    name: ReadOnly[str]
    systems: ReadOnly[list[str]]
    extensions: ReadOnly[dict[str, list[str]]]


CORES_MAP: Final[dict[str, CoreDict]] = {cores_map!s}
"""


class SystemCoreDict(TypedDict):
    name: str
    incompatible_extensions: list[str]


class SystemDict(TypedDict):
    name: str
    extensions: list[str]
    cores: dict[str, SystemCoreDict]


class CoreDict(TypedDict):
    name: str
    systems: list[str]
    extensions: dict[str, list[str]]


def _extensions(extensions: Iterable[str | int]) -> list[str]:
    return [str(extension) for extension in extensions]


if __name__ == '__main__':
    es_systems = cast(
        'dict[str, Any]',
        YAML(typ='safe').load(
            (_PARENT_DIR.parents[5] / 'emulationstation' / 'batocera-es-system' / 'es_systems.yml').read_text()
        ),
    )

    systems_map = cast(
        'dict[str, SystemDict]',
        {
            system_key: {
                'name': system_key,
                'extensions': _extensions(system_dict['extensions']),
                'cores': {
                    core_key: {
                        'name': core_key,
                        'incompatible_extensions': _extensions(core_dict['incompatible_extensions'])
                        if 'incompatible_extensions' in core_dict
                        else [],
                    }
                    for core_key, core_dict in system_dict['emulators']['libretro'].items()
                    if core_key != 'archs_include'
                },
            }
            for system_key, system_dict in es_systems.items()
            if 'emulators' in system_dict and 'libretro' in system_dict['emulators']
        },
    )

    cores_map: dict[str, CoreDict] = {}

    for system_name, system in systems_map.items():
        for core_name, core_dict in system['cores'].items():
            core: CoreDict = cores_map.setdefault(core_name, {'name': core_name, 'systems': [], 'extensions': {}})
            core['systems'].append(system_name)
            core['extensions'][system_name] = [
                extension for extension in system['extensions'] if extension not in core_dict['incompatible_extensions']
            ]

    (_PARENT_DIR / '_cores.py').write_text(_CORES_TEMPLATE.format(cores_map=cores_map))
    subprocess.run(['ruff', 'format', _PARENT_DIR / '_cores.py'])
