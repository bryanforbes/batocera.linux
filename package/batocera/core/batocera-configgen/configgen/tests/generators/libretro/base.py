from __future__ import annotations

import filecmp
from functools import wraps
from typing import TYPE_CHECKING, overload

import pytest
from pytest_lazy_fixtures import lf

from configgen.batoceraPaths import CONFIGS, ROMS
from configgen.generators.libretro.libretroGenerator import LibretroGenerator
from tests.generators.base import GeneratorBaseMixin
from tests.generators.libretro.utils import (
    get_configs,
    get_configs_from_base,
    get_first_extension,
    get_systems_for_core_iter,
)
from tests.mock_controllers import make_player_controller_list

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from unittest.mock import Mock

    from _pytest.fixtures import SubRequest
    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.controller import Controller
    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


@overload
def parametrize_guns[**P, R](func: Callable[P, R], /) -> Callable[P, R]: ...


@overload
def parametrize_guns[**P, R](
    *, systems: Iterable[str] | None = ..., metadata: Iterable[dict[str, str]] | None = ...
) -> Callable[[Callable[P, R]], Callable[P, R]]: ...


def parametrize_guns[**P, R](
    func: Callable[P, R] | None = None,
    /,
    *,
    systems: Iterable[str] | None = None,
    metadata: Iterable[dict[str, str]] | None = None,
) -> Callable[P, R] | Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @pytest.mark.parametrize(
            'controllers',
            [
                [lf('generic_xbox_pad')],
                [lf('generic_xbox_pad'), lf('ps3_controller'), lf('keyboard_controller'), lf('anbernic_pad')],
            ],
            ids=['1 controller', '4 controllers'],
        )
        @pytest.mark.parametrize_systems(systems)
        @pytest.mark.usefixtures(
            'controllers_config_guns_need_crosses',
            'system_guns_borders_size_name',
            'system_guns_border_ratio_type',
        )
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return func(*args, **kwargs)

        if metadata:
            wrapper = pytest.mark.parametrize('metadata', [{}, *metadata], ids=str)(wrapper)

        return wrapper

    if func:
        return decorator(func)

    return decorator


class LibretroBaseMixin:
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        return LibretroGenerator

    def assert_config_matches(self, snapshot: SnapshotAssertion) -> None:
        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='config')

    def assert_core_config_matches(self, snapshot: SnapshotAssertion) -> None:
        assert (CONFIGS / 'retroarch' / 'cores' / 'retroarch-core-options.cfg').read_text() == snapshot(
            name='core-config'
        )


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index')
class LibretroBaseCoreTest(GeneratorBaseMixin, LibretroBaseMixin):
    @pytest.fixture
    def core(self, request: SubRequest) -> str:
        core_marker = request.node.get_closest_marker('core')

        if core_marker is None:
            raise Exception('No core marker set')

        return core_marker.args[0]

    @pytest.fixture
    def system_name(self, core: str, request: SubRequest) -> str:
        system_name_marker = request.node.get_closest_marker('fallback_system_name')

        if system_name_marker is None:
            return next(get_systems_for_core_iter(core))

        return system_name_marker.args[0]

    @pytest.fixture
    def default_extension(self, mock_system: Emulator) -> str:
        return get_first_extension(mock_system.config['core'], mock_system.name)

    @pytest.fixture
    def metadata(self) -> dict[str, str]:
        return {}

    @pytest.fixture
    def controllers_config_guns_need_crosses(self, mocker: MockerFixture, request: SubRequest) -> Mock:
        return mocker.patch(
            'configgen.generators.libretro.libretroOptions.guns_need_crosses',
            return_value=getattr(request, 'param', False),
        )

    @pytest.fixture
    def system_guns_borders_size_name(self, mocker: MockerFixture, mock_system: Emulator) -> Mock:
        return mocker.patch.object(mock_system, 'guns_borders_size_name', return_value=None)

    @pytest.fixture
    def system_guns_border_ratio_type(self, mocker: MockerFixture, mock_system: Emulator) -> Mock:
        return mocker.patch.object(mock_system, 'guns_border_ratio_type', return_value=None)

    @pytest.mark.parametrize_systems
    def test_generate(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        assert (
            generator.generate(
                mock_system,
                ROMS / mock_system.name / f'rom.{default_extension}',
                [],
                {},
                [],
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)
        assert filecmp.cmp(
            CONFIGS / 'retroarch' / 'retroarchcustom.cfg',
            CONFIGS / 'retroarch' / 'config' / 'remaps' / 'common' / 'common.rmp',
        )

    @pytest.mark.parametrize(
        ('mock_system_config', 'get_gl_vendor', 'get_gl_version'),
        [
            pytest.param({'gfxbackend': 'gl'}, None, None, id='gl manual'),
            pytest.param({'gfxbackend': 'glcore'}, None, None, id='glcore manual'),
            pytest.param({'gfxbackend': 'vulkan'}, None, None, id='vulkan manual'),
            pytest.param({'gfxbackend': 'opengl'}, None, None, id='opengl manual'),  # for backwards compatibility
            pytest.param({}, 'amd', 3.1, id='auto, vendor amd, GL version 3.1'),
            pytest.param({}, 'nvidia', 3.1, id='auto, vendor nvidia, GL version 3.1'),
            pytest.param({}, 'unknown', 3.1, id='auto, vendor unknown, GL version 3.1'),
            pytest.param({}, 'amd', 3.0, id='auto, vendor amd, GL version 3.0'),
            pytest.param({}, 'nvidia', 3.0, id='auto, vendor nvidia, GL version 3.0'),
        ],
        indirect=['get_gl_vendor', 'get_gl_version'],
    )
    @pytest.mark.usefixtures('get_gl_vendor', 'get_gl_version')
    def test_generate_video_driver(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        vulkan_is_available: Mock,
        vulkan_has_discrete_gpu: Mock,
        vulkan_get_discrete_gpu_index: Mock,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        vulkan_is_available.return_value = True
        vulkan_has_discrete_gpu.return_value = True
        vulkan_get_discrete_gpu_index.return_value = '1234'

        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize_core_configs
    def test_generate_core_config(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)

    @pytest.mark.parametrize(
        ('mock_system_config', 'connected_to_internet'),
        [
            *(
                (config, connected_to_internet)
                for connected_to_internet in [True, False]
                for config in get_configs('retroachievements', ['0', '1'])
            ),
            *(
                (config, True)
                for config in get_configs_from_base(
                    {'retroachievements': '1'},
                    [
                        ('retroachievements.hardcore', ['0', '1']),
                        ('retroachievements.leaderboards', ['0', '1']),
                        ('retroachievements.verbose', ['0', '1']),
                        ('retroachievements.screenshot', ['0', '1']),
                        ('retroachievements.challenge_indicators', ['0', '1']),
                        ('retroachievements.encore', ['0', '1']),
                        ('retroachievements.richpresence', ['0', '1']),
                        ('retroachievements.unofficial', ['0', '1']),
                    ],
                )
            ),
        ],
        ids=str,
    )
    def test_generate_retroachievements(
        self,
        generator: Generator,
        mocker: MockerFixture,
        default_extension: str,
        connected_to_internet: bool,
        fs: FakeFilesystem,
        mock_system: Emulator,
        snapshot: SnapshotAssertion,
    ) -> None:
        mocker.patch(
            'configgen.generators.libretro.libretroConfig.connected_to_internet', return_value=connected_to_internet
        )

        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            [],
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )

        self.assert_config_matches(snapshot)

    @pytest.mark.parametrize_systems
    def test_generate_controllers(
        self,
        generator: Generator,
        fs: FakeFilesystem,
        default_extension: str,
        mock_system: Emulator,
        generic_xbox_pad: Controller,
        ps3_controller: Controller,
        keyboard_controller: Controller,
        anbernic_pad: Controller,
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(generic_xbox_pad, ps3_controller, keyboard_controller, anbernic_pad),
            {},
            [],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)

    @parametrize_guns
    def test_generate_guns(
        self,
        mocker: MockerFixture,
        generator: Generator,
        fs: FakeFilesystem,
        default_extension: str,
        mock_system: Emulator,
        metadata: dict[str, str],
        controllers: list[Controller],
        snapshot: SnapshotAssertion,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')

        mock_system.config['use_guns'] = '1'

        generator.generate(
            mock_system,
            ROMS / mock_system.name / f'rom.{default_extension}',
            make_player_controller_list(*controllers),
            metadata,
            [
                mocker.Mock(mouse_index=42),
                mocker.Mock(mouse_index=43),
                mocker.Mock(mouse_index=44),
                mocker.Mock(mouse_index=45),
            ],
            {},
            {'width': 1920, 'height': 1080},
        )
        self.assert_config_matches(snapshot)
        self.assert_core_config_matches(snapshot)
