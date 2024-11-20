from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cProfile import Profile

# 1) touch /var/run/emulatorlauncher.perf
# 2) start a game
# 3) gprof2dot.py -f pstats -n 5 /var/run/emulatorlauncher.prof -o emulatorlauncher.dot # wget https://raw.githubusercontent.com/jrfonseca/gprof2dot/master/gprof2dot.py
# 4) dot -Tpng emulatorlauncher.dot -o emulatorlauncher.png
# 3) or upload the file /var/run/emulatorlauncher.prof on https://nejc.saje.info/pstats-viewer.html


_profile: Profile | None = None

if os.path.exists('/var/run/emulatorlauncher.perf'):  # noqa: PTH110
    import cProfile

    _profile = cProfile.Profile()


def enable() -> None:
    if _profile:
        _profile.enable()


def disable(*, dump: bool = False) -> None:
    if _profile:
        _profile.disable()

        if dump:
            _profile.dump_stats('/var/run/emulatorlauncher.prof')
