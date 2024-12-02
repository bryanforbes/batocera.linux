from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest

from configgen.utils.wine import Runner

if TYPE_CHECKING:
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pytest_mock import MockerFixture


@pytest.fixture
def video_mode(mocker: MockerFixture) -> Mock:
    video_mode = mocker.Mock()
    video_mode.getRefreshRate.return_value = '60.0'
    mocker.patch.dict('sys.modules', {'configgen.utils.videoMode': video_mode})
    return video_mode


@pytest.fixture
def vulkan_is_available(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.is_available', return_value=getattr(request, 'param', False))


@pytest.fixture
def vulkan_has_discrete_gpu(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.has_discrete_gpu', return_value=getattr(request, 'param', False))


@pytest.fixture
def vulkan_get_discrete_gpu_uuid(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_discrete_gpu_uuid', return_value=getattr(request, 'param', None))


@pytest.fixture
def vulkan_get_discrete_gpu_index(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_discrete_gpu_index', return_value=getattr(request, 'param', None))


@pytest.fixture
def vulkan_get_discrete_gpu_name(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_discrete_gpu_name', return_value=getattr(request, 'param', None))


@pytest.fixture
def vulkan_get_version(mocker: MockerFixture, request: SubRequest) -> Any:
    return mocker.patch('configgen.utils.vulkan.get_version', return_value=getattr(request, 'param', ''))


@pytest.fixture
def wine_runner_install_wine_trick(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.wine.Runner.install_wine_trick')


@pytest.fixture
def wine_runner_regedit(mocker: MockerFixture) -> Mock:
    return mocker.patch('configgen.utils.wine.Runner.regedit')


@pytest.fixture
def wine_runner(mocker: MockerFixture, wine_runner_install_wine_trick: Mock, wine_runner_regedit: Mock) -> Mock:
    return mocker.patch('configgen.utils.wine.Runner', wraps=Runner)
