from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('uae4arm')
@pytest.mark.fallback_system_name('amiga500')
class TestLibretroGeneratorUae4Arm(LibretroBaseCoreTest): ...
