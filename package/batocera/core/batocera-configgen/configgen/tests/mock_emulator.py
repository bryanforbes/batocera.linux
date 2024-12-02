from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from configgen.config import Config, SystemConfig
from configgen.Emulator import Emulator

if TYPE_CHECKING:
    from collections.abc import Mapping


class MockEmulator(Emulator):
    def __init__(self, name: str, config: dict[str, Any] | None, renderconfig: dict[str, Any] | None = None) -> None:
        self.name = name
        self.config = SystemConfig(config or {})
        self.renderconfig = Config(renderconfig or {})


@pytest.fixture
def emulator() -> None:
    return


@pytest.fixture
def core() -> None:
    return


@pytest.fixture
def system_name() -> str:
    return 'unset'


@pytest.fixture
def mock_system_base_config(core: str | None, emulator: str, request: pytest.FixtureRequest) -> dict[str, Any]:
    core_marker = cast('pytest.Mark | None', request.node.get_closest_marker('core'))
    emulator_marker = cast('pytest.Mark | None', request.node.get_closest_marker('emulator'))

    if core_marker is not None:
        core = core_marker.args[0]

    if emulator_marker is not None:
        emulator = emulator_marker.args[0]

    return {
        'core': core or emulator,
        'emulator': emulator,
        'showFPS': False,
        'uimode': 'Full',
        'core-forced': False,
        'emulator-forced': False,
    }


@pytest.fixture
def mock_system_config() -> None:
    return


@pytest.fixture
def mock_system_render_config() -> dict[str, str]:
    return {}


@pytest.fixture
def mock_system(
    system_name: str,
    mock_system_base_config: Mapping[str, Any],
    mock_system_config: Mapping[str, Any] | None,
    mock_system_render_config: Mapping[str, Any],
    request: pytest.FixtureRequest,
) -> MockEmulator:
    config = dict(mock_system_base_config)

    mock_system_config_marker = cast('pytest.Mark | None', request.node.get_closest_marker('mock_system_config'))
    system_name_marker = cast('pytest.Mark | None', request.node.get_closest_marker('system_name'))

    if mock_system_config_marker is not None:
        config.update(mock_system_config_marker.args[0] or {})

    if system_name_marker is not None:
        system_name = system_name_marker.args[0]

    if mock_system_config:
        config.update(mock_system_config)

    renderconfig = dict(mock_system_render_config)
    mock_system_render_config_marker = cast(
        'pytest.Mark | None', request.node.get_closest_marker('mock_system_render_config')
    )

    if mock_system_render_config_marker is not None:
        renderconfig.update(mock_system_render_config_marker.args[0] or {})

    return MockEmulator(system_name, config=config, renderconfig=renderconfig)
