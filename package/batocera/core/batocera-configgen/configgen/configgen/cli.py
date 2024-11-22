from __future__ import annotations

import logging
import time
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any, TypedDict, TypeVar, Unpack, cast

import click

from . import profiler
from .emulators import run_emulator
from .utils.logger import setup_logging

_FC = TypeVar('_FC', bound=Callable[..., Any] | click.Command)

_logger = logging.getLogger(__name__)


def _player_callback(player: int, ctx: click.Context, option: click.Option, value: int | None) -> int | None:
    current_value: list[PlayerOptions] = ctx.params.setdefault('players', [])

    option_names = (
        f'p{player}hat_count',
        f'p{player}button_count',
        f'p{player}device_path',
        f'p{player}real_name',
        f'p{player}guid',
        f'p{player}index',
    )

    items = [
        (f'p{player}axis_count', value),
        *[(option_name, ctx.params.pop(option_name)) for option_name in option_names],
    ]

    if all(item[1] is not None for item in items):
        p_length = len(f'p{player}')
        current_value.append(
            cast(
                PlayerOptions,
                {
                    'player_number': player,
                    **{option_name[p_length:]: option_value for option_name, option_value in items},
                },
            )
        )
        return value

    if all(item[1] is None for item in items):
        return value

    raise click.UsageError(f'All options that start with p{player} must be specified if any are specified', ctx=ctx)


def _players(max_players: int) -> Callable[[_FC], _FC]:
    def wrap(callable: _FC) -> _FC:
        for n in range(max_players, 0, -1):
            callable = click.option(f'-p{n}nbaxes', f'p{n}axis_count', type=int, callback=partial(_player_callback, n))(
                callable
            )
            callable = click.option(f'-p{n}nbhats', f'p{n}hat_count', type=int)(callable)
            callable = click.option(f'-p{n}nbbuttons', f'p{n}button_count', type=int)(callable)
            callable = click.option(f'-p{n}devicepath', f'p{n}device_path', type=str)(callable)
            callable = click.option(f'-p{n}name', f'p{n}real_name', type=str)(callable)
            callable = click.option(f'-p{n}guid', type=str)(callable)
            callable = click.option(f'-p{n}index', type=int)(callable)

        return callable

    return wrap


class PlayerOptions(TypedDict):
    player_number: int
    index: int
    guid: str
    real_name: str
    device_path: str
    button_count: int
    hat_count: int
    axis_count: int


class Options(TypedDict):
    system: str
    rom: Path
    emulator: str | None
    core: str | None
    netplaymode: str | None
    netplaypass: str | None
    netplayip: str | None
    netplayport: str | None
    netplaysession: str | None
    state_slot: str | None
    state_filename: Path | None
    autosave: str | None
    systemname: str | None
    gameinfoxml: Path
    lightgun: bool
    wheel: bool
    trackball: bool
    spinner: bool
    players: list[PlayerOptions]


@click.command()
@click.option('-system', required=True)
@click.option('-rom', required=True, type=click.Path(path_type=Path))
@click.option('-emulator')
@click.option('-core')
@click.option('-netplaymode')
@click.option('-netplaypass')
@click.option('-netplayip')
@click.option('-netplayport')
@click.option('-netplaysession')
@click.option('-state_slot')
@click.option('-state_filename', type=click.Path(path_type=Path))
@click.option('-autosave')
@click.option('-systemname')
@click.option('-gameinfoxml', default='/dev/null', type=click.Path(path_type=Path))
@click.option('-lightgun', is_flag=True)
@click.option('-wheel', is_flag=True)
@click.option('-trackball', is_flag=True)
@click.option('-spinner', is_flag=True)
@_players(8)
def cli(**kwargs: Unpack[Options]) -> None:
    with setup_logging():
        exit_code = -1

        try:
            exit_code = run_emulator(kwargs)
        except Exception:
            _logger.exception('configgen exception: ')

        profiler.disable(dump=True)

        time.sleep(1)  # this seems to be required so that the gpu memory is restituated and available for es
        _logger.debug('Exiting configgen with status %s', exit_code)

        exit(exit_code)
