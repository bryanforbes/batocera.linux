from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, ClassVar, Literal, Self, TypeVar, overload

import yaml

from .batoceraPaths import BATOCERA_SHADERS, DEFAULTS_DIR, ES_SETTINGS, USER_SHADERS
from .utils.missing import MISSING, MissingType

if TYPE_CHECKING:
    from pathlib import Path

    from .cli import Options
    from .settings.unixSettings import UnixSettings

_T = TypeVar('_T')
_TV = TypeVar('_TV')
_FV = TypeVar('_FV')

_logger = logging.getLogger(__name__)


# adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def _dict_merge(destination: dict[str, Any], source: Mapping[str, Any]) -> None:
    """Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param destination: dict onto which the merge is executed
    :param source: dict merged into destination
    :return: None
    """
    for key, value in source.items():
        if key in destination and isinstance(destination[key], dict) and isinstance(value, Mapping):
            _dict_merge(destination[key], value)
        else:
            destination[key] = value


def _load_defaults(system: str, default_file: Path, default_arch_file: Path, /) -> dict[str, Any]:
    with default_file.open() as f:
        defaults: dict[str, Any] = yaml.load(f, Loader=yaml.CLoader)

    with default_arch_file.open() as f:
        arch_defaults: dict[str, Any] = yaml.load(f, Loader=yaml.CLoader) or {}

    config: dict[str, Any] = defaults.get('default', {})

    if 'default' in arch_defaults:
        _dict_merge(config, arch_defaults['default'])

    if system in defaults:
        _dict_merge(config, defaults[system])

    if system in arch_defaults:
        _dict_merge(config, arch_defaults[system])

    return config


@dataclass(slots=True)
class Config:
    TRUE_VALUES: ClassVar[set[Literal['1', 'true', 'on', 'enabled', True]]] = {'1', 'true', 'on', 'enabled', True}
    MISSING: ClassVar = MISSING

    data: dict[str, Any]

    def __contains__(self, x: object, /) -> bool:
        return x in self.data

    @overload
    def get(self, key: str, default: MissingType = ..., /) -> Any | MissingType: ...

    @overload
    def get(self, key: str, default: _T, /) -> Any | _T: ...

    def get(self, key: str, default: _T | MissingType = MISSING, /) -> Any | _T | MissingType:
        return self.data.get(key, default)

    @overload
    def get_bool(self, key: str, default: bool = False, /, *, return_values: None = None) -> bool: ...

    @overload
    def get_bool(self, key: str, default: bool = False, /, *, return_values: tuple[_TV, _FV]) -> _TV | _FV: ...

    def get_bool(
        self, key: str, default: bool = False, /, *, return_values: tuple[_TV, _FV] | None = None
    ) -> bool | _TV | _FV:
        value = self.get(key)

        if value is MISSING:
            return default

        if isinstance(value, str):
            value = value.lower()

        if return_values is None:
            return value in self.TRUE_VALUES

        return return_values[value not in self.TRUE_VALUES]

    @overload
    def get_str(self, key: str, default: MissingType = ..., /) -> str | MissingType: ...

    @overload
    def get_str(self, key: str, default: str, /) -> str: ...

    def get_str(self, key: str, default: str | MissingType = MISSING, /) -> str | MissingType:
        value = self.get(key)

        if value is MISSING:
            return default

        return str(value)

    @overload
    def get_int(self, key: str, default: MissingType = ..., /) -> int | MissingType: ...

    @overload
    def get_int(self, key: str, default: int, /) -> int: ...

    def get_int(self, key: str, default: int | MissingType = MISSING, /) -> int | MissingType:
        value = self.get(key)

        if value is MISSING:
            return default

        return int(value)

    @overload
    def get_float(self, key: str, default: MissingType = ..., /) -> float | MissingType: ...

    @overload
    def get_float(self, key: str, default: float, /) -> float: ...

    def get_float(self, key: str, default: float | MissingType = MISSING, /) -> float | MissingType:
        value = self.get(key)

        if value is MISSING:
            return default

        return float(value)

    def items(self, /, *, starts_with: str | None = None) -> Iterator[tuple[str, Any]]:
        if starts_with is None:
            yield from self.data.items()
        else:
            starts_with_len = len(starts_with)
            for key, value in self.data.items():
                if key.startswith(starts_with):
                    yield key[starts_with_len:], value


def _get_rom_settings_name(rom: Path, /) -> str:
    # sanitize rule by EmulationStation
    # see FileData::getConfigurationName() on batocera-emulationstation
    rom_settings_name = rom.name.replace('=', '').replace('#', '')

    _logger.info('game settings name: %s', rom_settings_name)

    return rom_settings_name


@dataclass
class SystemConfig(Config):
    @property
    def core(self) -> str:
        return self.data['core']

    @property
    def core_forced(self) -> str:
        return self.data['core-forced']

    @property
    def emulator(self) -> str:
        return self.data['emulator']

    @property
    def emulator_forced(self) -> str:
        return self.data['emulator-forced']

    @property
    def ui_mode(self) -> Literal['Full', 'Kiosk', 'Kid']:
        return self.data['uimode']

    @property
    def show_fps(self) -> bool:
        return self.data['showFPS']

    @property
    def video_mode(self) -> str:
        return self.data.get('videomode', 'default')

    @property
    def use_guns(self) -> bool:
        return self.get_bool('use_guns')

    @property
    def use_wheels(self) -> bool:
        return self.get_bool('use_wheels')

    @classmethod
    def load(cls, options: Options, settings: UnixSettings, /) -> Self:
        defaults = _load_defaults(
            options['system'], DEFAULTS_DIR / 'configgen-defaults.yml', DEFAULTS_DIR / 'configgen-defaults-arch.yml'
        )
        data: dict[str, Any] = {
            'emulator': defaults['emulator'],
            'core': defaults['core'],
        }

        # In the yaml files, the "options" structure is not flat, so we have to flatten it here
        # because the options are flat in batocera.conf to make it easier for end users to edit
        if 'options' in defaults:
            _dict_merge(data, defaults['options'])

        rom = options['rom']
        rom_settings_name = _get_rom_settings_name(rom)

        data.update(settings.get_all_iter('display', keep_name=True, keep_defaults=True))
        data.update(settings.get_all_iter('controllers', keep_name=True))

        global_settings = settings.get_all('global')
        system_settings = settings.get_all(options['system'])
        folder_settings = settings.get_all(f'{options["system"]}.folder["{rom.parent}"]')
        game_settings = settings.get_all(f'{options["system"]}["{rom_settings_name}"]')

        data.update(global_settings)
        data.update(system_settings)
        data.update(folder_settings)
        data.update(game_settings)

        try:
            es_config = ET.parse(ES_SETTINGS)

            # showFPS
            drawframerate_node = es_config.find("./bool[@name='DrawFramerate']")
            drawframerate_value = drawframerate_node.attrib['value'] if drawframerate_node is not None else 'false'
            if drawframerate_value not in ['false', 'true']:
                drawframerate_value = 'false'

            data['showFPS'] = drawframerate_value == 'true'

            # uimode
            uimode_node = es_config.find("./string[@name='UIMode']")
            uimode_value = uimode_node.attrib['value'] if uimode_node is not None else 'Full'
            if uimode_value not in ['Full', 'Kiosk', 'Kid']:
                uimode_value = 'Full'

            data['uimode'] = uimode_value
        except Exception:
            data['showFPS'] = False
            data['uimode'] = 'Full'

        data['emulator-forced'] = (
            'emulator' in global_settings
            or 'emulator' in system_settings
            or 'emulator' in game_settings
            or options['emulator'] is not None
        )
        data['core-forced'] = (
            'core' in global_settings
            or 'core' in system_settings
            or 'core' in game_settings
            or options['core'] is not None
        )

        if options['emulator'] is not None:
            data['emulator'] = options['emulator']

        if options['core'] is not None:
            data['core'] = options['core']

        if 'use_guns' not in data and options['lightgun']:
            data['use_guns'] = True

        if 'use_wheels' not in data and options['wheel']:
            data['use_wheels'] = True

        # network options
        if options['netplaymode'] is not None:
            data['netplay.mode'] = options['netplaymode']

        if options['netplaypass'] is not None:
            data['netplay.password'] = options['netplaypass']

        if options['netplayip'] is not None:
            data['netplay.server.ip'] = options['netplayip']

        if options['netplayport'] is not None:
            data['netplay.server.port'] = options['netplayport']

        if options['netplaysession'] is not None:
            data['netplay.server.session'] = options['netplaysession']

        # autosave arguments
        if options['state_slot'] is not None:
            data['state_slot'] = options['state_slot']

        if options['autosave'] is not None:
            data['autosave'] = options['autosave']

        if options['state_filename'] is not None:
            data['state_filename'] = options['state_filename']

        return cls(data)


@dataclass
class RenderConfig(Config):
    @classmethod
    def load(cls, options: Options, settings: UnixSettings, shader_set: str | MissingType, /) -> Self:
        data: dict[str, Any] = {}

        if shader_set is not cls.MISSING:
            if shader_set == 'none':
                rendering_defaults = BATOCERA_SHADERS / 'configs' / 'rendering-defaults.yml'
            else:
                rendering_defaults = USER_SHADERS / 'configs' / shader_set / 'rendering-defaults.yml'
                if not rendering_defaults.exists():
                    rendering_defaults = BATOCERA_SHADERS / 'configs' / shader_set / 'rendering-defaults.yml'

            data = _load_defaults(
                options['system'], rendering_defaults, rendering_defaults.with_name('rendering-defaults-arch.yml')
            )

        rom = options['rom']
        rom_settings_name = _get_rom_settings_name(rom)

        # es only allow to update system and game settings in fact for the moment

        # for compatibility with earlier Batocera versions, let's keep -renderer
        # but it should be reviewed when we refactor configgen (to Python3?)
        # so that we can fetch them from system.shader without -renderer
        data.update(settings.get_all_iter(f'{options["system"]}-renderer'))
        data.update(settings.get_all_iter(f'{options["system"]}["{rom_settings_name}"]-renderer'))

        return cls(data)
