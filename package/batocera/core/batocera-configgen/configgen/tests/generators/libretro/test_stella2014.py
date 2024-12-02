from __future__ import annotations

import pytest

from tests.generators.libretro.base import LibretroBaseCoreTest


@pytest.mark.core('stella2014')
class TestLibretroGeneratorStella2014(LibretroBaseCoreTest): ...
