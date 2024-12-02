from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('mednafen_ngp')
@pytest.mark.fallback_system_name('ngp')
class TestLibretroGeneratorMednafenNgp(LibretroBaseCoreTest): ...
