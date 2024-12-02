from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('zc210')
class TestLibretroGeneratorZC210(LibretroBaseCoreTest): ...
