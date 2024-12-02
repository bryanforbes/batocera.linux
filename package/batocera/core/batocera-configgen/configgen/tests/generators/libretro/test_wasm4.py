from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('wasm4')
class TestLibretroGeneratorWasm4(LibretroBaseCoreTest): ...
