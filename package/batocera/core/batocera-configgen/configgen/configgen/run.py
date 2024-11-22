from __future__ import annotations

from . import profiler

profiler.enable()


def run() -> None:
    from .cli import cli

    cli()


if __name__ == '__main__':
    run()
