from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, cast

import pytest

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(slots=True)
class MockEmulator:
    name: str
    config: dict[str, Any] = field(default_factory=dict)
    renderconfig: dict[str, Any] = field(default_factory=dict)

    def isOptSet(self, key):
        if key in self.config:  # noqa: SIM103
            return True
        else:
            return False

    def getOptBoolean(self, key):
        true_values = {'1', 'true', 'on', 'enabled', True}
        value = self.config.get(key)

        if isinstance(value, str):
            value = value.lower()

        return value in true_values

    def getOptString(self, key):
        if key in self.config:  # noqa: SIM102
            if self.config[key]:
                return self.config[key]
        return ''


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
        'showFPS': 'false',
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
