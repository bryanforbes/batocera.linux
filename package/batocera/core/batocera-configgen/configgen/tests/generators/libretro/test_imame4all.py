from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('imame4all')
@pytest.mark.fallback_system_name('mame')
class TestLibretroGeneratoriMame4All(LibretroBaseCoreTest): ...
