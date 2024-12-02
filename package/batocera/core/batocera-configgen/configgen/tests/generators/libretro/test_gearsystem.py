from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('gearsystem')
@pytest.mark.fallback_system_name('mastersystem')
class TestLibretroGeneratorGearSystem(LibretroBaseCoreTest): ...
