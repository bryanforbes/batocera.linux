from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.config import SystemConfig

if TYPE_CHECKING:
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.generators.Generator import Generator


class GeneratorBaseMixin:
    @pytest.fixture
    def generator(self, generator_cls: type[Generator]) -> Generator:
        return generator_cls()


class GeneratorBaseTest(GeneratorBaseMixin):
    def test_get_resolution_mode(self, mocker: MockerFixture, generator: Generator) -> None:
        assert (
            generator.getResolutionMode(SystemConfig({'videomode': mocker.sentinel.videomode}))
            == mocker.sentinel.videomode
        )

    def test_get_mouse_mode(self, generator: Generator) -> None:
        assert not generator.getMouseMode(SystemConfig({}), Path())

    def test_execution_directory(self, generator: Generator) -> None:
        assert generator.executionDirectory(SystemConfig({}), Path()) is None

    def test_supports_internal_bezels(self, generator: Generator) -> None:
        assert not generator.supportsInternalBezels()

    def test_has_internal_mangohud_call(self, generator: Generator) -> None:
        assert not generator.hasInternalMangoHUDCall()

    def test_get_in_game_ratio(self, generator: Generator) -> None:
        assert generator.getInGameRatio(SystemConfig({}), {'width': 1920, 'height': 1080}, Path()) == 4 / 3

    def test_get_hotkeys_context(self, generator: Generator, snapshot: SnapshotAssertion) -> None:
        assert generator.getHotkeysContext() == snapshot
