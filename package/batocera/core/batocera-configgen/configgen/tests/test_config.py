from __future__ import annotations

from typing import Any

import pytest

from configgen.config import Config, SystemConfig
from configgen.utils.missing import MISSING


class TestConfig:
    def test_init(self) -> None:
        data = {'foo': 1, 'bar': 2}
        assert Config(data).data is data

    def test_contains(self) -> None:
        config = Config({'foo': 1, 'bar': 2})

        assert 'foo' in config
        assert 'bar' in config
        assert 'baz' not in config

    def test_getitem(self) -> None:
        config = Config({'foo': 1, 'bar': 2})

        assert config['foo'] == 1
        assert config['bar'] == 2

        with pytest.raises(KeyError):
            config['baz']

    def test_setitem(self) -> None:
        config = Config({})

        config['foo'] = 42

        assert config['foo'] == 42

    def test_delitem(self) -> None:
        config = Config({'foo': 1})

        del config['foo']

        assert 'foo' not in config

    def test_get(self) -> None:
        config = Config({'foo': 1, 'bar': None})

        assert config.get('foo') == 1
        assert config.get('bar') is None
        assert config.get('baz') is MISSING
        assert config.get('ham', 'spam') == 'spam'

    @pytest.mark.parametrize('value', ['1', 'On', 'tRue', 'enAblEd', pytest.param(True, id='boolean True')])
    def test_get_bool_true(self, value: Any) -> None:
        assert Config({'key': value}).get_bool('key') is True

    def test_get_bool_false(self) -> None:
        config = Config({'key': 'asdf'})

        assert config.get_bool('key') is False
        assert config.get_bool('baz') is False

    def test_get_bool_default(self) -> None:
        config = Config({})

        assert config.get_bool('baz', True) is True

    def test_get_bool_return_values(self) -> None:
        config = Config({'foo': '1', 'bar': '0'})

        assert config.get_bool('foo', return_values=('yes', 'no')) == 'yes'
        assert config.get_bool('bar', return_values=('yes', 'no')) == 'no'
        assert config.get_bool('baz', return_values=('yes', 'no')) == 'no'
        assert config.get_bool('baz', True, return_values=('yes', 'no')) == 'yes'

    def test_get_str(self) -> None:
        config = Config({'foo': 1, 'bar': True})

        assert config.get_str('foo') == '1'
        assert config.get_str('bar') == 'True'
        assert config.get_str('baz') is MISSING
        assert config.get_str('baz', 'blah') == 'blah'

    def test_get_int(self) -> None:
        config = Config({'foo': '10', 'bar': True})

        assert config.get_int('foo') == 10
        assert config.get_int('bar') == 1
        assert config.get_int('baz') is MISSING
        assert config.get_int('baz', 42) == 42

    def test_get_float(self) -> None:
        config = Config({'foo': '10.1', 'bar': True})

        assert config.get_float('foo') == 10.1
        assert config.get_float('bar') == 1.0
        assert config.get_float('baz') is MISSING
        assert config.get_float('baz', 42.3) == 42.3

    def test_items(self) -> None:
        assert dict(Config({'foo': 1, 'bar': 2}).items()) == {'foo': 1, 'bar': 2}

    def test_items_starts_with(self) -> None:
        assert dict(Config({'foo.bar': 1, 'foo.baz': 2, 'ham.spam': 3}).items(starts_with='foo.')) == {
            'bar': 1,
            'baz': 2,
        }

    def test_keys(self) -> None:
        assert list(Config({'foo': 1, 'bar': 2, 'baz': 3}).keys()) == ['foo', 'bar', 'baz']

    def test_values(self) -> None:
        assert list(Config({'foo': 1, 'bar': 2, 'baz': 3}).values()) == [1, 2, 3]


class TestSystemConfig:
    def test_init(self) -> None:
        config = SystemConfig({})

        assert isinstance(config, Config)

    def test_properties(self) -> None:
        config = SystemConfig(
            {
                'emulator': 'foo',
                'emulator-forced': True,
                'core': 'bar',
                'core-forced': False,
                'uimode': 'Full',
                'showFPS': True,
                'use_guns': False,
                'use_wheels': True,
            }
        )

        assert config.emulator == 'foo'
        assert config.emulator_forced
        assert config.core == 'bar'
        assert not config.core_forced
        assert config.ui_mode == 'Full'
        assert config.show_fps
        assert not config.use_guns
        assert config.use_wheels
        assert config.video_mode == 'default'

        config['videomode'] = 'something'
        assert config.video_mode == 'something'
