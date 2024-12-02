from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

import pytest

from configgen.batoceraPaths import BIOS
from tests.generators.libretro._cores import CORES_MAP
from tests.generators.libretro.base import LibretroBaseCoreTest
from tests.generators.libretro.utils import CoreDict, get_systems_for_core

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from _pytest.mark import ParameterSet  # pyright: ignore[reportPrivateImportUsage]
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture

    from configgen.Emulator import Emulator


type _ConfigSpec = dict[str, str | list[str]]

_DATA_DIR: Final = Path(__file__).parents[4] / 'data'

pytestmark = pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index')


def _make_config_param(
    core: str, system_name: str, config: dict[str, Any], include_system_name: bool, /
) -> ParameterSet:
    return pytest.param(
        core,
        system_name,
        config,
        id=f'{system_name}-{config}' if include_system_name else f'{config}',
    )


def _get_config_params(
    core: str, system_name: str, specs: Iterable[_ConfigSpec], include_system_name: bool, /
) -> Iterator[ParameterSet]:
    for spec in specs:
        if len(spec) == 1:
            key, value = next(iter(spec.items()))
            if isinstance(value, list):
                yield from (_make_config_param(core, system_name, {key: v}, include_system_name) for v in value)
            else:
                yield _make_config_param(core, system_name, spec, include_system_name)
        else:
            yield _make_config_param(core, system_name, spec, include_system_name)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if not metafunc.cls or not issubclass(metafunc.cls, LibretroBaseCoreTest):
        return

    core_mark = metafunc.definition.get_closest_marker('core')

    if core_mark is None:
        return

    core: str = core_mark.args[0]
    systems = get_systems_for_core(core)

    if parametrize_systems_mark := metafunc.definition.get_closest_marker('parametrize_systems'):
        if len(systems) > 1:
            systems = (
                parametrize_systems_mark.args[0]
                if parametrize_systems_mark.args
                else parametrize_systems_mark.kwargs.get('systems')
            ) or systems
            metafunc.parametrize('system_name', systems)

    elif core_configs_mark := metafunc.definition.get_closest_marker('parametrize_core_configs'):
        include_system_name = len(systems) > 1
        configs = core_configs_mark.args[0] if core_configs_mark.args else core_configs_mark.kwargs.get('configs')
        system_configs = (
            core_configs_mark.args[1]
            if len(core_configs_mark.args) > 1
            else core_configs_mark.kwargs.get('system_configs')
        )

        params: list[ParameterSet] = []

        for system_name in systems:
            if metafunc.definition.name == 'test_generate_core_config':
                params.extend(
                    _get_config_params(
                        core,
                        system_name,
                        [
                            {'rewind': ['0', '1']},
                            {'runahead': ['0', '1']},
                            {'runahead': '1', 'preemptiveframes': '0'},
                            {'runahead': '1', 'preemptiveframes': '1'},
                            {'runahead': '1', 'secondinstance': '0'},
                            {'runahead': '1', 'secondinstance': '1'},
                        ],
                        include_system_name,
                    )
                )

            if configs:
                params.extend(_get_config_params(core, system_name, configs, include_system_name))

            if system_configs and (configs_for_system := system_configs.get(system_name)):
                params.extend(_get_config_params(core, system_name, configs_for_system, include_system_name))

            if metafunc.definition.name != 'test_generate_core_config' and not configs and not system_configs:
                params.extend(_get_config_params(core, system_name, [{}], include_system_name))

        metafunc.parametrize(('core', 'system_name', 'mock_system_config'), params)


@pytest.fixture
def emulator() -> str:
    return 'libretro'


@pytest.fixture
def core_data(mock_system: Emulator) -> CoreDict | None:
    return CORES_MAP.get(mock_system.config['core'])


@pytest.fixture(autouse=True)
def fs(fs: FakeFilesystem, mock_system: Emulator) -> FakeFilesystem:
    fs.add_real_directory(_DATA_DIR, target_path='/usr/share/batocera/configgen/data')
    fs.create_dir(BIOS)
    fs.create_file(f'/usr/share/libretro/info/{mock_system.config["core"]}_libretro.info')

    return fs


@pytest.fixture(autouse=True)
def get_devices_information(mocker: MockerFixture, request: SubRequest) -> Mock:
    mock = mocker.patch(
        'configgen.controllersConfig.getDevicesInformation',
        return_value=getattr(request, 'param', {}),
    )
    mocker.patch(
        'configgen.generators.libretro.libretroControllers.getDevicesInformation',
        new=mock,
    )
    return mock


@pytest.fixture(autouse=True)
def get_associated_mouse(mocker: MockerFixture, request: SubRequest) -> Mock:
    mock = mocker.patch(
        'configgen.controllersConfig.getAssociatedMouse',
        return_value=getattr(request, 'param', None),
    )
    mocker.patch(
        'configgen.generators.libretro.libretroControllers.getAssociatedMouse',
        new=mock,
    )
    return mock


@pytest.fixture
def get_games_metadata(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch(
        'configgen.controllersConfig.getGamesMetaData',
        return_value=getattr(request, 'param', None) or {},
    )


@pytest.fixture
def guns_need_crosses(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch(
        'configgen.generators.libretro.libretroOptions.guns_need_crosses',
        return_value=getattr(request, 'param', True),
    )


@pytest.fixture
def get_gl_vendor(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch(
        'configgen.utils.videoMode.getGLVendor', return_value=getattr(request, 'param', None) or 'unknown'
    )


@pytest.fixture
def get_gl_version(mocker: MockerFixture, request: SubRequest) -> Mock:
    return mocker.patch('configgen.utils.videoMode.getGLVersion', return_value=getattr(request, 'param', None) or 0)
