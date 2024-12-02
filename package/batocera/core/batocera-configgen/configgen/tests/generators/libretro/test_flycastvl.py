from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('flycastvl')
@pytest.mark.fallback_system_name('dreamcast')
class TestLibretroGeneratorFlycastvl(LibretroBaseCoreTest): ...
