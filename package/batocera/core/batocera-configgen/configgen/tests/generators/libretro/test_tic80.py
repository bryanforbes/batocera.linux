from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('tic80')
class TestLibretroGeneratorTic80(LibretroBaseCoreTest): ...
