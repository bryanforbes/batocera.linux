from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('gong')
class TestLibretroGeneratorGong(LibretroBaseCoreTest): ...
