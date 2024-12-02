from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('fmsx')
@pytest.mark.fallback_system_name('msx1')
class TestLibretroGeneratorFmsx(LibretroBaseCoreTest): ...
