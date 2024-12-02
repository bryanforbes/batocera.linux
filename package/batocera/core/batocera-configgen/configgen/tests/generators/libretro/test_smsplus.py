from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('smsplus')
@pytest.mark.fallback_system_name('mastersystem')
class TestLibretroGeneratorSmsPlus(LibretroBaseCoreTest): ...
