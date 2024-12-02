from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mame')
@pytest.mark.fallback_system_name('mame')
class TestLibretroGeneratorMame(LibretroBaseCoreTest): ...
