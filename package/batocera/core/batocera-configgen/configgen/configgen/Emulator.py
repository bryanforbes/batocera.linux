from __future__ import annotations

import collections.abc
import logging
import xml.etree.ElementTree as ET
from dataclasses import InitVar, dataclass, field
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar, overload

import yaml

from .batoceraPaths import BATOCERA_CONF, BATOCERA_SHADERS, DEFAULTS_DIR, ES_SETTINGS, USER_SHADERS
from .settings.unixSettings import UnixSettings
from .utils.missing import MISSING, MissingType

if TYPE_CHECKING:
    from pathlib import Path
    from typing_extensions import deprecated

    from .gun import GunMapping

_logger = logging.getLogger(__name__)
_T = TypeVar('_T')
_TV = TypeVar('_TV')
_FV = TypeVar('_FV')


# adapted from https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
def _dict_merge(destination: dict[str, Any], source: collections.abc.Mapping[str, Any]) -> None:
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param destination: dict onto which the merge is executed
    :param source: dict merged into destination
    :return: None
    """
    for key, value in source.items():
        if (key in destination and isinstance(destination[key], dict) and isinstance(value, collections.abc.Mapping)):
            _dict_merge(destination[key], value)
        else:
            destination[key] = value


@dataclass(slots=True)
class Emulator:
    TRUE_VALUES: ClassVar[set[Literal['1', 'true', 'on', 'enabled', True]]] = {'1', 'true', 'on', 'enabled', True}
    MISSING: ClassVar = MISSING

    name: str
    rom: InitVar[Path]

    config: dict[str, Any] = field(init=False)
    renderconfig: dict[str, Any] = field(init=False)

    def __post_init__(self, rom: Path, /) -> None:
        # read the configuration from the system name
        self.config = self.__get_system_config(
            DEFAULTS_DIR / "configgen-defaults.yml",
            DEFAULTS_DIR / "configgen-defaults-arch.yml"
        )
        if "emulator" not in self.config or not self.config["emulator"]:
            _logger.error("no emulator defined. exiting.")
            raise Exception("No emulator found")

        gsname = self.game_settings_name(rom)

        # load configuration from batocera.conf
        batoceraSettings = UnixSettings(BATOCERA_CONF)
        globalSettings = batoceraSettings.load_all('global')
        controllersSettings = batoceraSettings.load_all('controllers', includeName=True)
        systemSettings = batoceraSettings.load_all(self.name)
        folderSettings = batoceraSettings.load_all(f'{self.name}.folder["{rom.parent}"]')
        gameSettings = batoceraSettings.load_all(f'{self.name}["{gsname}"]')

        # add some other options
        displaySettings = batoceraSettings.load_all('display')
        for opt, value in displaySettings.items():
            self.config[f"display.{opt}"] = value

        # update config
        Emulator.update_configuration(self.config, controllersSettings)
        Emulator.update_configuration(self.config, globalSettings)
        Emulator.update_configuration(self.config, systemSettings)
        Emulator.update_configuration(self.config, folderSettings)
        Emulator.update_configuration(self.config, gameSettings)
        self.updateFromESSettings()
        _logger.debug("uimode: %s", self.config['uimode'])

        # forced emulators ?
        self.config["emulator-forced"] = False
        self.config["core-forced"] = False
        if "emulator" in globalSettings or "emulator" in systemSettings or "emulator" in gameSettings:
            self.config["emulator-forced"] = True
        if "core" in globalSettings or "core" in systemSettings or "core" in gameSettings:
            self.config["core-forced"] = True

        # update renderconfig
        self.renderconfig = {}
        if "shaderset" in self.config:
            if self.config["shaderset"] != "none":
                rendering_defaults = USER_SHADERS / "configs" / str(self.config["shaderset"]) / "rendering-defaults.yml"
                if rendering_defaults.exists():
                    self.renderconfig = self.__get_yaml_defaults(
                        rendering_defaults,
                        rendering_defaults.with_name("rendering-defaults-arch.yml")
                    )
                else:
                    rendering_defaults = BATOCERA_SHADERS / "configs" / str(self.config["shaderset"]) / "rendering-defaults.yml"
                    self.renderconfig = self.__get_yaml_defaults(
                        rendering_defaults,
                        rendering_defaults.with_name("rendering-defaults-arch.yml")
                    )
            elif self.config["shaderset"] == "none":
                rendering_defaults = BATOCERA_SHADERS / "configs" / "rendering-defaults.yml"
                self.renderconfig = self.__get_yaml_defaults(
                    rendering_defaults,
                    rendering_defaults.with_name("rendering-defaults-arch.yml")
                )

        # for compatibility with earlier Batocera versions, let's keep -renderer
        # but it should be reviewed when we refactor configgen (to Python3?)
        # so that we can fetch them from system.shader without -renderer
        systemSettings = batoceraSettings.load_all(f'{self.name}-renderer')
        gameSettings = batoceraSettings.load_all(f'{self.name}["{gsname}"]-renderer')

        # es only allow to update systemSettings and gameSettings in fact for the moment
        Emulator.update_configuration(self.renderconfig, systemSettings)
        Emulator.update_configuration(self.renderconfig, gameSettings)

    @property
    def core(self) -> str:
        return self.config['core']

    @property
    def core_forced(self) -> bool:
        return self.config['core-forced']

    @property
    def emulator(self) -> str:
        return self.config['emulator']

    @property
    def emulator_forced(self) -> bool:
        return self.config['emulator-forced']

    @property
    def ui_mode(self) -> Literal['Full', 'Kiosk', 'Kid']:
        return self.config['uimode']

    @property
    def show_fps(self) -> bool:
        return self.config['showFPS']

    def game_settings_name(self, rom: Path) -> str:
        # sanitize rule by EmulationStation
        # see FileData::getConfigurationName() on batocera-emulationstation
        gs_name = rom.name.replace('=','')
        gs_name = gs_name.replace('#','')
        _logger.info("game settings name: %s", gs_name)
        return gs_name

    def __get_yaml_defaults(self, default_yaml: Path, default_arch_yaml: Path, /) -> dict[str, Any]:
        with default_yaml.open() as f:
            defaults: dict[str, Any] = yaml.load(f, Loader=yaml.CLoader)

        arch_defaults: dict[str, Any] = {}
        if default_arch_yaml.exists():
            with default_arch_yaml.open() as f:
                loaded_arch_defaults = yaml.load(f, Loader=yaml.CLoader)

            if loaded_arch_defaults is not None:
                arch_defaults = loaded_arch_defaults

        config: dict[str, Any] = {}

        if 'default' in defaults:
            config = defaults['default']

        if 'default' in arch_defaults:
            _dict_merge(config, arch_defaults['default'])

        if self.name in defaults:
            _dict_merge(config, defaults[self.name])

        if self.name in arch_defaults:
            _dict_merge(config, arch_defaults[self.name])

        return config

    def __get_system_config(self, default_yaml: Path, default_arch_yaml: Path, /) -> dict[str, Any]:
        defaults = self.__get_yaml_defaults(default_yaml, default_arch_yaml)

        result: dict[str, Any] = { 'emulator': defaults['emulator'], 'core': defaults['core'] }

        # In the yaml files, the "options" structure is not flat, so we have to flatten it here
        # because the options are flat in batocera.conf to make it easier for end users to edit
        if 'options' in defaults:
            _dict_merge(result, defaults['options'])

        return result

    def has_option(self, key: str, /) -> bool:
        return key in self.config

    @overload
    def get_option(self, key: str, default: MissingType = ..., /) -> Any | MissingType:
        ...

    @overload
    def get_option(self, key: str, default: _T, /) -> Any | _T:
        ...

    def get_option(self, key: str, default: _T | MissingType = MISSING, /) -> Any | _T | MissingType:
        return self.config.get(key, default)

    @overload
    def get_option_bool(self, key: str, default: bool = False, /, *, return_values: None = None) -> bool:
        ...

    @overload
    def get_option_bool(self, key: str, default: bool = False, /, *, return_values: tuple[_TV, _FV]) -> _TV | _FV:
        ...

    def get_option_bool(self, key: str, default: bool = False, /, *, return_values: tuple[_TV, _FV] | None = None) -> bool | _TV | _FV:
        value = self.config.get(key, MISSING)

        if value is MISSING:
            return default

        if isinstance(value, str):
            value = value.lower()

        if return_values is None:
            return value in self.TRUE_VALUES
        else:
            return return_values[value not in self.TRUE_VALUES]

    @overload
    def get_option_str(self, key: str, default: MissingType = ..., /) -> str | MissingType:
        ...

    @overload
    def get_option_str(self, key: str, default: str, /) -> str:
        ...

    def get_option_str(self, key: str, default: str | MissingType = MISSING, /) -> str | MissingType:
        value = self.config.get(key, MISSING)

        if value is MISSING:
            return default

        return str(value)

    @overload
    def get_option_int(self, key: str, default: MissingType = ..., /) -> int | MissingType:
        ...

    @overload
    def get_option_int(self, key: str, default: int, /) -> int:
        ...

    def get_option_int(self, key: str, default: int | MissingType = MISSING, /) -> int | MissingType:
        value = self.config.get(key, MISSING)

        if value is MISSING:
            return default

        return int(value)

    @overload
    def get_option_float(self, key: str, default: MissingType = ..., /) -> float | MissingType:
        ...

    @overload
    def get_option_float(self, key: str, default: float, /) -> float:
        ...

    def get_option_float(self, key: str, default: float | MissingType = MISSING, /) -> float | MissingType:
        value = self.config.get(key, MISSING)

        if value is MISSING:
            return default

        return float(value)

    def option_items(self, /, *, starts_with: str | None = None) -> collections.abc.Iterator[tuple[str, Any]]:
        if starts_with is None:
            yield from self.config.items()
        else:
            starts_with_len = len(starts_with)
            for key, value in self.config.items():
                if key.startswith(starts_with):
                    yield key[starts_with_len:], value


    if TYPE_CHECKING:
        @deprecated('Use has_option()')
        def isOptSet(self, key: str) -> bool:
            ...

        @deprecated('Use get_option_bool()')
        def getOptBoolean(self, key: str) -> bool:
            ...

        @deprecated('Use get_option_str()')
        def getOptString(self, key: str) -> str:
            ...
    else:
        def isOptSet(self, key: str) -> bool:
            return key in self.config

        def getOptBoolean(self, key: str) -> bool:
            value = self.config.get(key)

            if isinstance(value, str):
                value = value.lower()

            return value in self.TRUE_VALUES

        def getOptString(self, key: str) -> str:
            if key in self.config:  # noqa: SIM102
                if self.config[key]:
                    return self.config[key]
            return ""

    def get_guns_borders_size(self, guns: GunMapping, /) -> str | None:
        borders_size = self.get_option_str("controllers.guns.borderssize", "medium")

        # overriden by specific options
        borders_mode = "normal"
        if (config_borders_mode := self.get_option_str("controllers.guns.bordersmode", "auto")) != "auto":
            borders_mode = config_borders_mode
        if (config_borders_mode := self.get_option_str("bordersmode", "auto")) != "auto":
            borders_mode = config_borders_mode

        # others are gameonly and normal
        if borders_mode == "hidden":
            return None

        if borders_mode == "force":
            return borders_size

        for gun in guns.values():
            if gun.need_borders:
                return borders_size

        return None

    def get_guns_borders_ratio(self, guns: GunMapping, /) -> str | None:
        # returns None to follow the bezel overlay size by default
        return self.get_option("controllers.guns.bordersratio", None)

    @staticmethod
    def update_configuration(config: dict[str, Any], settings: dict[str, Any], /) -> None:
        # ignore all values "default", "auto", "" to take the system value instead
        # ideally, such value must not be in the configuration file
        # but historically some users have them

        config.update({
            key: value for key, value in settings.items()
            if value and value != 'default' and value != 'auto'
        })

    # fps value is from es
    def updateFromESSettings(self):
        try:
            esConfig = ET.parse(ES_SETTINGS)

            # showFPS
            drawframerate_node = esConfig.find("./bool[@name='DrawFramerate']")
            drawframerate_value = drawframerate_node.attrib["value"] if drawframerate_node is not None else 'false'
            if drawframerate_value not in ['false', 'true']:
                drawframerate_value = 'false'

            self.config['showFPS'] = drawframerate_value == 'true'

            # uimode
            uimode_node = esConfig.find("./string[@name='UIMode']")
            uimode_value = uimode_node.attrib["value"] if uimode_node is not None else 'Full'
            if uimode_value not in ['Full', 'Kiosk', 'Kid']:
                uimode_value = 'Full'

            self.config['uimode'] = uimode_value

        except Exception:
            self.config['showFPS'] = False
            self.config['uimode'] = "Full"
