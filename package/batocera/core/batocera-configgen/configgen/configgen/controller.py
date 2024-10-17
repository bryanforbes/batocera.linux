from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, Self, TypeAlias, TypedDict, Unpack, cast

from .batoceraPaths import BATOCERA_ES_DIR, USER_ES_DIR
from .input import Input, InputDict

if TYPE_CHECKING:
    import argparse

"""Default mapping of Batocera keys to SDL_GAMECONTROLLERCONFIG keys."""
_DEFAULT_SDL_MAPPING: Final = {
    'b': 'a',
    'a': 'b',
    'x': 'y',
    'y': 'x',
    'l2': 'lefttrigger',
    'r2': 'righttrigger',
    'l3': 'leftstick',
    'r3': 'rightstick',
    'pageup': 'leftshoulder',
    'pagedown': 'rightshoulder',
    'start': 'start',
    'select': 'back',
    'up': 'dpup',
    'down': 'dpdown',
    'left': 'dpleft',
    'right': 'dpright',
    'joystick1up': 'lefty',
    'joystick1left': 'leftx',
    'joystick2up': 'righty',
    'joystick2left': 'rightx',
    'hotkey': 'guide'
}


def _key_to_sdl_game_controller_config(keyname: str, name: str, type: str, id: str, value: str) -> str | None:
    """
    Converts a key mapping to the SDL_GAMECONTROLLER format.

    Arguments:
      keyname: (str) SDL_GAMECONTROLLERCONFIG input name.
      name: (str) `es_input.cfg` input name.
      type: (str) 'button', 'hat', or 'axis'
      id: (int) Numeric key id.
      value: (int) Hat value. Only used if type == 'hat' or type == 'axis' and 'joystick' in name.
    Returns:
      (str) SDL_GAMECONTROLLERCONFIG-formatted key mapping string.
    Examples:
      _keyToSdlGameControllerConfig('leftshoulder', 'l1', 'button', 6)
        'leftshoulder:b6'

      _keyToSdlGameControllerConfig('dpleft', 'left', 'hat', 0, 8)
        'dpleft:h0.8'

      _keyToSdlGameControllerConfig('lefty', 'joystick1up', 'axis', 1, -1)
        'lefty:a1'

      _keyToSdlGameControllerConfig('lefty', 'joystick1up', 'axis', 1, 1)
        'lefty:a1~'

      _keyToSdlGameControllerConfig('dpup', 'up', 'axis', 1, -1)
        'dpup:-a1'
    """
    if type == 'button':
        return f'{keyname}:b{id}'
    elif type == 'hat':
        return f'{keyname}:h{id}.{value}'
    elif type == 'axis':
        if 'joystick' in name:
            return f"{keyname}:a{id}{'~' if int(value) > 0 else ''}"
        elif keyname in ('dpup', 'dpdown', 'dpleft', 'dpright'):
            return f"{keyname}:{'-' if int(value) < 0 else '+'}a{id}"
        else:
            return f'{keyname}:a{id}'
    elif type == 'key':
        return None
    else:
        raise ValueError(f'unknown key type: {type!r}')


class _ControllerChanges(TypedDict, total=False):
    guid: str
    player: int | None
    index: int
    real_name: str
    device_path: str | None
    button_count: int | None
    hat_count: int | None
    axis_count: int | None
    physical_device_path: str | None
    physical_id: int | None


@dataclass(slots=True, kw_only=True)
class Controller:
    device_name: str
    type: Literal['keyboard', 'joystick']
    guid: str
    player: int | None
    index: int = -1
    real_name: str = ""
    inputs: InputDict = field(default_factory=dict)
    device_path: str | None = None
    button_count: int | None = None
    hat_count: int | None = None
    axis_count: int | None = None
    physical_device_path: str | None = None
    physical_id: int | None = None

    @property
    def uid_name(self) -> str:
        return self.guid + self.device_name

    def replace(self, /, **changes: Unpack[_ControllerChanges]) -> Self:
        return replace(self, **changes)

    def generate_sdl_game_db_line(self, sdl_mapping: Mapping[str, str] = _DEFAULT_SDL_MAPPING, /) -> str:
        config = [self.guid, self.real_name, 'platform:Linux']

        def add_mapping(input: Input) -> None:
            key_name = sdl_mapping.get(input.name, None)
            if key_name is None:
                return
            sdl_config = _key_to_sdl_game_controller_config(key_name, input.name, input.type, input.id, input.value)
            if sdl_config is not None:
                config.append(sdl_config)

        hotkey_input: Input | None = None
        mapped_button_ids: set[str] = set()
        for input in self.inputs.values():
            if input.name is None:
                continue
            if input.name == 'hotkey':
                hotkey_input = input
                continue
            if input.type == 'button':
                mapped_button_ids.add(input.id)

            add_mapping(input)

        if hotkey_input is not None and hotkey_input.id not in mapped_button_ids:
            add_mapping(hotkey_input)

        config.append('')

        return ','.join(config)

    @classmethod
    def from_element(cls, element: ET.Element, /) -> Self:
        return cls(
            device_name=cast(str, element.get("deviceName")),
            type=cast(Literal['keyboard', 'joystick'], element.get("type")),
            guid=cast(str, element.get("deviceGUID")),
            player=None,
            index=-1,
            inputs=Input.from_parent_element(element)
        )

    @classmethod
    def parse_all(cls) -> list[Self]:
        return [
            cls.from_element(controller)
            for conffile in [BATOCERA_ES_DIR / "es_input.cfg", USER_ES_DIR / 'es_input.cfg'] if conffile.exists()
            for controller in ET.parse(conffile).getroot().findall(".//inputConfig")
        ]

    @classmethod
    def load_all(cls) -> dict[str, Self]:
        return {controller.uid_name: controller for controller in cls.parse_all()}

    @classmethod
    def load_for_players(cls, max_players: int, args: argparse.Namespace, /) -> dict[int, Self]:
        controllers: dict[int, Self] = {}
        all_controllers = cls.load_all()

        for player_number in range(1, max_players + 1):
            controller = cls.find_best_controller_config(all_controllers, args, player_number)
            if controller is not None:
                controllers[player_number] = controller

        return controllers

    @classmethod
    def find_best_controller_config(
        cls, controllers: Mapping[str, Self], args: argparse.Namespace, player_number: int, /,
    ) -> Self | None:
        player_index: int | None = getattr(args, f'p{player_number}index')

        if player_index is None:
            return None

        player_guid: str = getattr(args, f'p{player_number}guid')
        player_name: str = getattr(args, f'p{player_number}name')
        player_device_path: str = getattr(args, f'p{player_number}devicepath')
        player_buttons: int = getattr(args, f'p{player_number}nbbuttons')
        player_hats: int = getattr(args, f'p{player_number}nbhats')
        player_axes: int = getattr(args, f'p{player_number}nbaxes')

        for controller in controllers.values():
            if controller.guid == player_guid and controller.device_name == player_name:
                return controller.replace(
                    guid=player_guid,
                    player=player_number,
                    index=player_index,
                    real_name=player_name,
                    device_path=player_device_path,
                    button_count=player_buttons,
                    hat_count=player_hats,
                    axis_count=player_axes,
                )

        for controller in controllers.values():
            if controller.guid == player_guid:
                return controller.replace(
                    guid=player_guid,
                    player=player_number,
                    index=player_index,
                    real_name=player_name,
                    device_path=player_device_path,
                    button_count=player_buttons,
                    hat_count=player_hats,
                    axis_count=player_axes,
                )

        for controller in controllers.values():
            if controller.device_name == player_name:
                return controller.replace(
                    guid=player_guid,
                    player=player_number,
                    index=player_index,
                    real_name=player_name,
                    device_path=player_device_path,
                    button_count=player_buttons,
                    hat_count=player_hats,
                    axis_count=player_axes,
                )

        return None


ControllerMapping: TypeAlias = Mapping[str, Controller]
ControllerDict: TypeAlias = Mapping[str, Controller]
ControllerPlayerMapping: TypeAlias = Mapping[int, Controller]
ControllerPlayerDict: TypeAlias = dict[int, Controller]


def generate_sdl_game_controller_config(controllers: ControllerPlayerMapping, /) -> str:
    return '\n'.join([controller.generate_sdl_game_db_line() for controller in controllers.values()])

def write_sdl_controller_db(
    controllers: ControllerPlayerMapping, output_file: str | Path = '/tmp/gamecontrollerdb.txt', /,
) -> Path:
    output_file = Path(output_file)
    with output_file.open('w') as text_file:
        text_file.write(generate_sdl_game_controller_config(controllers))
    return output_file
