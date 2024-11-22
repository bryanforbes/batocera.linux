from __future__ import annotations

from contextlib import nullcontext
from importlib import import_module
from typing import TYPE_CHECKING, Final

from ..batoceraPaths import BATOCERA_CONF
from ..config import RenderConfig, SystemConfig
from ..controller import Controller
from ..controllersConfig import getGamesMetaData
from ..gun import Gun, precalibrate_guns
from ..settings.unixSettings import UnixSettings
from ..utils.squashfs import squashfs_rom
from ..utils.wheels import configure_wheels
from ._base import Emulator as Emulator  # noqa: TCH001

if TYPE_CHECKING:
    from ..cli import Options

_GENERATOR_MAP: Final[dict[str, str]] = {}


def get_emulator_cls(emulator: str, /) -> type[Emulator]:
    module_path = _GENERATOR_MAP.get(emulator, emulator.replace('-', '_'))

    try:
        module = import_module(f'..{module_path}', package=__name__)
        emulator_cls: type[Emulator] = module.Emulator
    except ImportError as e:
        if e.name is not None and e.name.startswith(__name__.split('.')[0]):
            raise Exception(f'no emulator found for {emulator!r}') from e

        raise
    except AttributeError as e:
        raise Exception(f'no emulator found for {emulator!r}') from e

    return emulator_cls


def run_emulator(options: Options, /) -> int:
    exit_code = -1
    original_rom = options['rom']

    if original_rom.suffix == '.squashfs':
        rom_context_manager = squashfs_rom(original_rom)
    else:
        rom_context_manager = nullcontext(original_rom)

    with rom_context_manager as rom:
        system = options['system']

        settings = UnixSettings(BATOCERA_CONF)
        system_config = SystemConfig.load(options, settings)
        render_config = RenderConfig.load(options, settings, system_config.get('shaderset'))

        metadata = getGamesMetaData(system, original_rom)

        controllers = Controller.load_for_player_options(options['players'])

        if system_config.use_guns:
            guns = Gun.get_all()
            precalibrate_guns(system, system_config.emulator, system_config.core, original_rom)
        else:
            guns = {}

        with configure_wheels(controllers, system, system_config, metadata) as (controllers, wheels):
            emulator_cls = get_emulator_cls(system_config.emulator)
            emulator = emulator_cls(system, system_config, render_config, metadata, controllers, guns, wheels)
            exit_code = emulator.run(rom, original_rom, options['gameinfoxml'])

    return exit_code
