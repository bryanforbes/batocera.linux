from __future__ import annotations

import filecmp
import shutil
from typing import TYPE_CHECKING, cast

import pytest

from configgen.batoceraPaths import CONFIGS, ROMS
from tests.generators.base import GeneratorBaseMixin
from tests.generators.libretro.utils import (
    get_configs,
    get_configs_from_base,
    get_first_extension,
    get_systems_for_core_iter,
)

if TYPE_CHECKING:
    from unittest.mock import Mock

    from pyfakefs.fake_filesystem import FakeFilesystem
    from pytest_mock import MockerFixture
    from syrupy.assertion import SnapshotAssertion

    from configgen.Emulator import Emulator
    from configgen.generators.Generator import Generator


class LibretroBaseMixin:
    @pytest.fixture
    def generator_cls(self) -> type[Generator]:
        from configgen.generators.libretro.libretroGenerator import LibretroGenerator

        return LibretroGenerator


@pytest.mark.usefixtures('vulkan_is_available', 'vulkan_has_discrete_gpu', 'vulkan_get_discrete_gpu_index')
class LibretroBaseCoreTest(GeneratorBaseMixin, LibretroBaseMixin):
    @pytest.fixture
    def core(self, request: pytest.FixtureRequest) -> str:
        core_marker = cast('pytest.Mark | None', request.node.get_closest_marker('core'))

        if core_marker is None:
            raise Exception('No core marker set')

        return core_marker.args[0]

    @pytest.fixture
    def system_name(self, core: str, request: pytest.FixtureRequest) -> str:
        system_name_marker = cast('pytest.Mark | None', request.node.get_closest_marker('fallback_system_name'))

        if system_name_marker is None:
            return next(get_systems_for_core_iter(core))

        return system_name_marker.args[0]

    @pytest.fixture
    def default_extension(self, mock_system: Emulator) -> str:
        return get_first_extension(mock_system.config['core'], mock_system.name)

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
                f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
            )
            == snapshot
        )
        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='retroarchcustom')
        assert (CONFIGS / 'retroarch' / 'cores' / 'retroarch-core-options.cfg').read_text() == snapshot(
            name='corecustom'
        )
        assert filecmp.cmp(
            CONFIGS / 'retroarch' / 'retroarchcustom.cfg',
            CONFIGS / 'retroarch' / 'config' / 'remaps' / 'common' / 'common.rmp',
        )

    def test_generate_missing_info(
        self,
        generator: Generator,
        default_extension: str,
        fs: FakeFilesystem,
        mock_system: Emulator,
    ) -> None:
        fs.create_file(ROMS / mock_system.name / f'rom.{default_extension}')
        shutil.rmtree('/usr/share/libretro/info')

        with pytest.raises(
            Exception, match=rf'^missing file /usr/share/libretro/info/{mock_system.config["core"]}_libretro.info'
        ):
            generator.generate(
                mock_system,
                f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
                {},
                {},
                {},
                {},
                {'width': 1920, 'height': 1080},
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
            f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='retroarchcustom')

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
            f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )
        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='retroarchcustom')
        assert (CONFIGS / 'retroarch' / 'cores' / 'retroarch-core-options.cfg').read_text() == snapshot(
            name='corecustom'
        )

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
            f'/userdata/roms/{mock_system.name}/rom.{default_extension}',
            {},
            {},
            {},
            {},
            {'width': 1920, 'height': 1080},
        )

        assert (CONFIGS / 'retroarch' / 'retroarchcustom.cfg').read_text() == snapshot(name='retroarchcustom')
