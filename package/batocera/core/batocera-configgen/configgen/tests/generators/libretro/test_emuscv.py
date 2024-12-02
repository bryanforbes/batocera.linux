from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('emuscv')
class TestLibretroGeneratorEmuscv(LibretroBaseCoreTest): ...
