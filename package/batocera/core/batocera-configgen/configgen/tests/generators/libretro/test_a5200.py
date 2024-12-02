from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('a5200')
class TestLibretroGeneratorA5200(LibretroBaseCoreTest): ...
