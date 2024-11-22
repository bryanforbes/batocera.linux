from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
from abc import ABC, abstractmethod
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, cast

from .. import profiler
from ..batoceraPaths import (
    SAVES,
    SYSTEM_DECORATIONS,
    SYSTEM_SCRIPTS,
    USER_DECORATIONS,
    USER_SCRIPTS,
    mkdir_if_not_exists,
)
from ..controller import Controller, ControllerDict, generate_sdl_game_controller_config, write_sdl_controller_db
from ..utils import videoMode
from ..utils.bezels import (
    BezelInfos,
    createTransparentBezel,
    fast_image_size,
    gunBorderImage,
    gunBordersSize,
    gunsBordersColorFomConfig,
    resizeImage,
    tatooImage,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from types import FrameType

    from ..config import RenderConfig, SystemConfig
    from ..gun import GunDict
    from ..types import BezelInfo, DeviceInfoDict, HotkeysContext, Resolution
    from ..utils.missing import MissingType

_logger = logging.getLogger(__name__)


@dataclass(slots=True)
class Emulator(ABC):
    system: str
    config: SystemConfig
    render_config: RenderConfig
    metadata: Mapping[str, str]
    controllers: ControllerDict
    guns: GunDict
    wheels: DeviceInfoDict

    resolution: Resolution = field(init=False)
    process: subprocess.Popen | None = field(init=False)

    hotkeys_context: ClassVar[HotkeysContext]

    @property
    def name(self) -> str:
        return self.config.emulator

    @property
    def core(self) -> str:
        return self.config.core

    @property
    def sorted_controllers(self) -> list[Controller]:
        return sorted(self.controllers.values())

    @property
    def resolution_mode(self) -> str:
        return self.config.video_mode

    @property
    def supports_internal_bezels(self) -> bool:
        return False

    @property
    def start_mango_hud(self) -> bool:
        return True

    def get_mouse_mode(self, rom: Path, /) -> bool:
        return False

    def get_execution_directory(self, rom: Path, /) -> Path | None:
        return None

    def get_in_game_ratio(self, rom: Path, /) -> float:
        return 4 / 3

    def __post_init__(self) -> None:
        signal.signal(signal.SIGINT, self.__kill)

    @abstractmethod
    def generate(self, rom: Path, /) -> tuple[list[str | Path], dict[str, str | Path]]: ...

    def generate_sdl_game_controller_config(self) -> str:
        return generate_sdl_game_controller_config(self.controllers)

    def write_sdl_controller_db(self, output_file: str | Path = '/tmp/gamecontrollerdb.txt', /) -> Path:
        return write_sdl_controller_db(self.controllers, output_file)

    def get_guns_borders_size(self) -> str | None:
        borders_size = self.config.get_str('controllers.guns.borderssize', 'medium')

        # overriden by specific options
        borders_mode = 'normal'
        if (config_borders_mode := self.config.get_str('controllers.guns.bordersmode', 'auto')) != 'auto':
            borders_mode = config_borders_mode
        if (config_borders_mode := self.config.get_str('bordersmode', 'auto')) != 'auto':
            borders_mode = config_borders_mode

        # others are gameonly and normal
        if borders_mode == 'hidden':
            return None

        if borders_mode == 'force':
            return borders_size

        for gun in self.guns.values():
            if gun.need_borders:
                return borders_size

        return None

    def get_guns_borders_ratio(self) -> str | None:
        # returns None to follow the bezel overlay size by default
        return self.config.get('controllers.guns.bordersratio', None)

    def get_bezel_infos(self, rom: Path, bezel: str, emulator: str | None = None, /) -> BezelInfos | None:
        # by order choose :
        # rom name in the system subfolder of the user directory (gb/mario.png)
        # rom name in the system subfolder of the system directory (gb/mario.png)
        # rom name in the user directory (mario.png)
        # rom name in the system directory (mario.png)
        # system name with special graphic in the user directory (gb-90.png)
        # system name in the user directory (gb.png)
        # system name with special graphic in the system directory (gb-90.png)
        # system name in the system directory (gb.png)
        # default name (default.png)
        # else return
        # mamezip files are for MAME-specific advanced artwork (bezels with overlays and backdrops, animated LEDs, etc)
        alt_decoration = videoMode.getAltDecoration(self.system, rom, emulator if emulator is not None else self.name)

        rom_base = rom.stem  # filename without extension

        user_bezel_dir = USER_DECORATIONS / bezel
        user_games_dir = user_bezel_dir / 'games'
        user_systems_dir = user_bezel_dir / 'systems'
        system_bezel_dir = SYSTEM_DECORATIONS / bezel
        system_games_dir = system_bezel_dir / 'games'
        system_systems_dir = system_bezel_dir / 'systems'

        bezels_to_try = [
            (rom_base, user_games_dir / self.system, None, True),
            (rom_base, system_games_dir / self.system, user_games_dir / self.system, True),
            (rom_base, user_games_dir, None, True),
            (rom_base, system_games_dir, user_games_dir, True),
            (f'{self.system}-{alt_decoration}' if alt_decoration != '0' else None, user_systems_dir, None, False),
            (self.system, user_systems_dir, None, False),
            (f'{self.system}-{alt_decoration}' if alt_decoration != '0' else None, system_systems_dir, None, False),
            (self.system, system_systems_dir, None, False),
            (f'default-{alt_decoration}', user_bezel_dir, None, True),
            ('default.png', user_bezel_dir, None, True),
            (f'default-{alt_decoration}', system_bezel_dir, None, True),
            ('default.png', system_bezel_dir, None, True),
        ]

        for stem, directory, alt_directory, specific_to_game in bezels_to_try:
            if stem and (png := directory / stem).exists():
                alt_png = png if alt_directory is None else (alt_directory / png.name)
                _logger.debug('Original bezel file used: %s', png)
                return {
                    'png': png,
                    'info': png.with_suffix('.info'),
                    'layout': alt_png.with_suffix('.lay'),
                    'mamezip': alt_png.with_suffix('.zip'),
                    'specific_to_game': specific_to_game,
                }

        return None

    def run(self, rom: Path, original_rom: Path, game_info_xml: Path, /) -> int:
        exit_code = -1

        # the resolution must be changed before configuration while the configuration may depend on it (ie bezels)
        with self.__change_resolution(), self.__change_mouse(rom):
            # savedir: create the save directory if not already done
            mkdir_if_not_exists(SAVES / self.system)

            # SDL VSync is a big deal on OGA and RPi4
            os.environ.update({'SDL_RENDER_VSYNC': self.config.get_bool('sdlvsync', True, return_values=('1', '0'))})

            # run a script before emulator starts
            self.__call_script(SYSTEM_SCRIPTS, 'gameStart', self.core or '', rom)
            self.__call_script(USER_SCRIPTS, 'gameStart', self.core or '', rom)

            from ..utils.evmapy import evmapy

            with (
                evmapy(self.name, self.system, self.core, original_rom, self.controllers, self.guns),
                self.__set_hotkeygen_context(),
            ):
                if execution_directory := self.get_execution_directory(rom):
                    os.chdir(execution_directory)

                args, env = self.generate(rom)

                if hud_config_file := self.__setup_hud(rom, game_info_xml):
                    env.update(
                        {
                            'MANGOHUD_DLSYM': '1',
                            'MANGOHUD_CONFIGFILE': hud_config_file,
                        }
                    )

                    if self.start_mango_hud:
                        args.insert(0, 'mangohud')

                profiler.disable()
                self.__run(args, env)
                profiler.enable()

            # run a script after emulator shuts down
            self.__call_script(USER_SCRIPTS, 'gameStop', self.core or '', rom)
            self.__call_script(SYSTEM_SCRIPTS, 'gameStop', self.core or '', rom)

        return exit_code

    def __run(self, args: list[str | Path], environment: dict[str, str | Path], /) -> int:
        exit_code = -1

        # compute environment : first the current envs, then override by values set at generator level
        env: dict[str, str | Path] = dict(os.environ)
        env.update(environment)

        _logger.debug('command args: %s', args)
        _logger.debug('command env: %s', env)

        if args:
            self.process = subprocess.Popen(args, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            return exit_code

        try:
            out, err = self.process.communicate()
            exit_code = self.process.returncode
            _logger.debug(out.decode())
            _logger.error(err.decode())
        except BrokenPipeError:
            # Seeing BrokenPipeError? This is probably caused by head truncating output in the front-end
            # Examine es-core/src/platform.cpp::runSystemCommand for additional context
            pass
        except:  # noqa: E722
            _logger.error('emulator exited')

        return exit_code

    def __kill(self, signal: int, frame: FrameType | None) -> None:
        _logger.debug('Exiting')
        if self.process:
            _logger.debug('Killing process')
            self.process.kill()

    @contextmanager
    def __change_resolution(self) -> Iterator[None]:
        wanted_game_mode = self.resolution_mode
        system_mode = videoMode.getCurrentMode()
        resolution_changed = False

        try:
            # lower the resolution if mode is auto
            new_system_mode = system_mode  # newsystemmode is the mode after minmax (ie in 1K if tv was in 4K), systemmode is the mode before (ie in es)
            if not self.config.video_mode or self.config.video_mode == 'default':
                _logger.debug('minTomaxResolution')
                _logger.debug('video mode before minmax: %s', system_mode)
                videoMode.minTomaxResolution()
                new_system_mode = videoMode.getCurrentMode()
                if new_system_mode != system_mode:
                    resolution_changed = True

            _logger.debug('current video mode: %s', new_system_mode)
            _logger.debug('wanted video mode: %s', wanted_game_mode)

            if wanted_game_mode != 'default' and wanted_game_mode != new_system_mode:
                videoMode.changeMode(wanted_game_mode)
                resolution_changed = True

            resolution = videoMode.getCurrentResolution()

            # if resolution is reversed (ie ogoa boards), reverse it in resolution to have it correct
            if videoMode.isResolutionReversed():
                resolution['width'], resolution['height'] = resolution['height'], resolution['width']

            _logger.debug('resolution: %sx%s', resolution['width'], resolution['height'])

            self.resolution = resolution

            yield
        finally:
            # always restore the resolution
            if resolution_changed:
                try:
                    videoMode.changeMode(system_mode)
                except Exception:
                    pass  # don't fail

    @contextmanager
    def __change_mouse(self, rom: Path, /) -> Iterator[None]:
        mode_changed = False

        try:
            if self.get_mouse_mode(rom):
                mode_changed = True
                videoMode.changeMouse(True)

            yield
        finally:
            if mode_changed:
                try:
                    videoMode.changeMouse(False)
                except Exception:
                    pass  # don't fail

    @contextmanager
    def __set_hotkeygen_context(self) -> Iterator[None]:
        context = self.hotkeys_context
        _logger.debug('hotkeygen: updating context to %s', context['name'])
        subprocess.call(['hotkeygen', '--new-context', context['name'], json.dumps(context['keys'])])

        try:
            yield
        finally:
            # reset hotkeygen context
            _logger.debug('hotkeygen: resetting to default context')
            subprocess.call(['hotkeygen', '--default-context'])

    def __call_script(self, directory: Path, event: str, *args: str | Path) -> None:
        if not directory.is_dir():
            return

        for file in directory.iterdir():
            if file.is_dir():
                self.__call_script(file, event, *args)
            else:
                if os.access(file, os.X_OK):
                    _logger.debug('calling external script: %s', [file, event, self.system, self.name, *args])
                    subprocess.call([file, event, self.system, self.name, *args])

    def __setup_hud(self, rom: Path, game_info_xml: Path, /) -> Path | None:
        if not self.config.get_bool('hud_support') or self.supports_internal_bezels:
            return None

        hud = self.config.get_str('hud')
        hud_bezel = self.__get_hud_bezel(rom)
        if (not hud or hud == 'none') and hud_bezel is None:
            return None

        hud_config = self.__get_hud_config(game_info_xml, hud, hud_bezel)
        hud_config_file = Path('/var/run/hud.config')
        hud_config_file.write_text(hud_config)

        return hud_config_file

    def __get_hud_bezel(self, rom: Path, /) -> Path | None:
        bezel = self.config.get('bezel')
        bezel_tattoo = self.config.get('bezel.tattoo', '0')
        borders_size = self.get_guns_borders_size()

        # no good reason for a bezel
        if (not bezel or bezel == 'none') and bezel_tattoo == '0' and borders_size is None:
            return None

        if not bezel or bezel == 'none':
            overlay_png_file = Path('/tmp/bezel_transhud_black.png')
            overlay_info_file = Path('/tmp/bezel_transhud_black.info')
            createTransparentBezel(overlay_png_file, self.resolution['width'], self.resolution['height'])

            w = self.resolution['width']
            h = self.resolution['height']
            overlay_info_file.write_text(
                f'{{ "width":{w}, "height":{h}, "opacity":1.0000000, "messagex":0.220000, "messagey":0.120000 }}'
            )
        else:
            _logger.debug('hud enabled. trying to apply the bezel %s', bezel)

            bz_infos = self.get_bezel_infos(rom, bezel)
            if bz_infos is None:
                _logger.debug('no bezel info file found')
                return None

            overlay_info_file = bz_infos['info']
            overlay_png_file = bz_infos['png']

        # check the info file
        # bottom, top, left and right must not cover too much the image to be considered as compatible
        if overlay_info_file.exists():
            try:
                infos = cast('BezelInfo', json.loads(overlay_info_file.read_text()))
            except Exception:
                _logger.warning('unable to read %s', overlay_info_file)
                infos = {}
        else:
            infos = {}

        if 'width' in infos and 'height' in infos:
            bezel_width = cast(int, infos['width'])
            bezel_height = cast(int, infos['height'])
            _logger.info('bezel size read from %s', overlay_info_file)
        else:
            bezel_width, bezel_height = fast_image_size(overlay_png_file)
            _logger.info('bezel size read from %s', overlay_png_file)

        # max cover proportion and ratio distortion
        max_cover = 0.05  # 5%
        max_ratio_delta = 0.01

        screen_ratio = self.resolution['width'] / self.resolution['height']
        bezel_ratio = bezel_width / bezel_height

        # the screen and bezel ratio must be approximatly the same
        if borders_size is None and abs(screen_ratio - bezel_ratio) > max_ratio_delta:
            _logger.debug(
                'screen ratio (%(screen_ratio)s) is too far from the bezel one (%(bezel_ratio)s) : %(screen_ratio)s - %(bezel_ratio)s > %(max_ratio_delta)s',
                {'screen_ratio': screen_ratio, 'bezel_ratio': bezel_ratio, 'max_ratio_delta': max_ratio_delta},
            )
            return None

        # the ingame image and the bezel free space must feet
        ## the bezel top and bottom cover must be minimum
        # in case there is a border, force it
        if borders_size is None:
            if 'top' in infos and infos['top'] / bezel_height > max_cover:
                _logger.debug(
                    'bezel top covers too much the game image : %s / %s > %s', infos['top'], bezel_height, max_cover
                )
                return None
            if 'bottom' in infos and infos['bottom'] / bezel_height > max_cover:
                _logger.debug(
                    'bezel bottom covers too much the game image : %s / %s > %s',
                    infos['bottom'],
                    bezel_height,
                    max_cover,
                )
                return None

        # if there is no information about top/bottom, assume default is 0

        ## the bezel left and right cover must be maximum
        in_game_ratio = self.get_in_game_ratio(rom)
        img_height = bezel_height
        img_width = img_height * in_game_ratio

        if 'left' not in infos:
            _logger.debug('bezel has no left info in %s', overlay_info_file)
            # assume default is 4/3 over 16/9
            infos_left = (bezel_width - (bezel_height / 3 * 4)) / 2
            if borders_size is None and abs((infos_left - ((bezel_width - img_width) / 2.0)) / img_width) > max_cover:
                _logger.debug(
                    'bezel left covers too much the game image : %s / %s > %s',
                    infos_left - ((bezel_width - img_width) / 2.0),
                    img_width,
                    max_cover,
                )
                return None

        if 'right' not in infos:
            _logger.debug('bezel has no right info in %s', overlay_info_file)
            # assume default is 4/3 over 16/9
            infos_right = (bezel_width - (bezel_height / 3 * 4)) / 2
            if borders_size is None and abs((infos_right - ((bezel_width - img_width) / 2.0)) / img_width) > max_cover:
                _logger.debug(
                    'bezel right covers too much the game image : %s / %s > %s',
                    infos_right - ((bezel_width - img_width) / 2.0),
                    img_width,
                    max_cover,
                )
                return None

        if borders_size is None:
            if 'left' in infos and abs((infos['left'] - ((bezel_width - img_width) / 2.0)) / img_width) > max_cover:
                _logger.debug(
                    'bezel left covers too much the game image : %s / %s > %s',
                    infos['left'] - ((bezel_width - img_width) / 2.0),
                    img_width,
                    max_cover,
                )
                return None
            if 'right' in infos and abs((infos['right'] - ((bezel_width - img_width) / 2.0)) / img_width) > max_cover:
                _logger.debug(
                    'bezel right covers too much the game image : %s / %s > %s',
                    infos['right'] - ((bezel_width - img_width) / 2.0),
                    img_width,
                    max_cover,
                )
                return None

        # if screen and bezel sizes doesn't match, resize
        # stretch option
        bezel_stretch = self.config.get_bool('bezel_stretch')
        if bezel_width != self.resolution['width'] or bezel_height != self.resolution['height']:
            _logger.debug('bezel needs to be resized')
            output_png_file = Path('/tmp/bezel.png')
            try:
                resizeImage(
                    overlay_png_file,
                    output_png_file,
                    self.resolution['width'],
                    self.resolution['height'],
                    bezel_stretch,
                )
            except Exception as e:
                _logger.error('failed to resize the image %s', e)
                return None
            overlay_png_file = output_png_file

        if bezel_tattoo != '0':
            output_png_file = Path('/tmp/bezel_tattooed.png')
            tatooImage(overlay_png_file, output_png_file, self)
            overlay_png_file = output_png_file

        # borders
        if borders_size is not None:
            _logger.debug('Draw gun borders')
            output_png_file = Path('/tmp/bezel_gunborders.png')
            inner_size, outer_size = gunBordersSize(borders_size)
            borders_ratio = self.get_guns_borders_ratio()
            _logger.debug('Gun border ratio = %s', borders_ratio)
            gunBorderImage(
                overlay_png_file,
                output_png_file,
                borders_ratio,
                inner_size,
                outer_size,
                gunsBordersColorFomConfig(self.config.data),
            )
            overlay_png_file = output_png_file

        _logger.debug('applying bezel %s', overlay_png_file)
        return overlay_png_file

    def __get_hud_config(self, game_info_xml: Path, mode: str | MissingType, bezel: Path | None, /) -> str:
        hud_config = ''

        if bezel is not None:
            hud_config = f'background_image={bezel}\nlegacy_layout=false\n'

        if mode is self.config.MISSING or mode == 'none':
            return f'{hud_config}background_alpha=0\n'  # hide the background

        match self.config.get('hud_corner'):
            case 'NW':
                hud_position = 'top-left'
            case 'NE':
                hud_position = 'top-right'
            case 'SE':
                hud_position = 'bottom-right'
            case _:
                hud_position = 'bottom-left'

        emulator = self.name
        if emulator != self.core and self.core:
            emulator += f'/{self.core}'

        game_info = _get_game_info(game_info_xml)

        game_name = game_info.get('name', '')
        game_thumbnail = game_info.get('thumbnail', '')

        # predefined values
        if mode == 'perf':
            hud_config += f'position={hud_position}\nbackground_alpha=0.9\nlegacy_layout=false\ncustom_text=%GAMENAME%\ncustom_text=%SYSTEMNAME%\ncustom_text=%EMULATORCORE%\nfps\ngpu_name\nengine_version\nvulkan_driver\nresolution\nram\ngpu_stats\ngpu_temp\ncpu_stats\ncpu_temp\ncore_load'
        elif mode == 'game':
            hud_config += f'position={hud_position}\nbackground_alpha=0\nlegacy_layout=false\nfont_size=32\nimage_max_width=200\nimage=%THUMBNAIL%\ncustom_text=%GAMENAME%\ncustom_text=%SYSTEMNAME%\ncustom_text=%EMULATORCORE%'
        elif mode == 'custom' and (hud_custom := self.config.get_str('hud_custom')):
            hud_config += hud_custom.replace('\\n', '\n')
        else:
            hud_config = f'{hud_config}background_alpha=0\n'  # hide the background

        hud_config = hud_config.replace('%SYSTEMNAME%', self.system or '')
        hud_config = hud_config.replace('%GAMENAME%', game_name or '')
        hud_config = hud_config.replace('%EMULATORCORE%', emulator or '')
        return hud_config.replace('%THUMBNAIL%', game_thumbnail or '')


def _get_game_info(xml: Path) -> dict[str, str]:
    import xml.etree.ElementTree as ET

    game_info: dict[str, str] = {}

    try:
        infos = ET.parse(xml)
        try:
            game_info['name'] = cast('str', cast('ET.Element', infos.find('./game/name')).text)
        except Exception:
            pass
        try:
            game_info['thumbnail'] = cast('str', cast('ET.Element', infos.find('./game/thumbnail')).text)
        except Exception:
            pass
    except Exception:
        pass

    return game_info
