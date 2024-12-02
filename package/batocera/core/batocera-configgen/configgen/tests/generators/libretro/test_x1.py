from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('x1')
class TestLibretroGeneratorX1(LibretroBaseCoreTest): ...
