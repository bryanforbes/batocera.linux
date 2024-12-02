from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from configgen.settings.unixSettings import UnixSettings

if TYPE_CHECKING:
    from pyfakefs.fake_filesystem import FakeFilesystem
    from syrupy.assertion import SnapshotAssertion


@pytest.mark.usefixtures('fs')
class TestUnixSettings:
    def test_read(self, fs: FakeFilesystem, snapshot: SnapshotAssertion) -> None:
        fs.create_file(
            '/tmp/test.ini',
            contents="""foo.bar = 1
foo.baz = 2
spam.ham = 3
spam.bam = 4
""",
        )
        settings = UnixSettings(Path('/tmp/test.ini'))

        assert settings.config.defaults() == snapshot

    def test_write(self, snapshot: SnapshotAssertion, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)

        settings = UnixSettings('/tmp/test.ini')
        settings.save('foo', 'bar')
        settings.save('spam', 1)
        settings.save('somepassword', '1234thisisreallysecure')
        settings.write()

        assert Path('/tmp/test.ini').read_text() == snapshot
        assert caplog.record_tuples == snapshot(name='logging')

    def test_separator(self, snapshot: SnapshotAssertion) -> None:
        settings = UnixSettings('/tmp/test.ini', separator='\t')
        settings.save('foo', 'bar')
        settings.save('spam', 1)
        settings.save('somepassword', '1234thisisreallysecure')
        settings.write()

        assert Path('/tmp/test.ini').read_text() == snapshot

    def test_disable_all(self, snapshot: SnapshotAssertion, caplog: pytest.LogCaptureFixture) -> None:
        caplog.set_level(logging.DEBUG)

        settings = UnixSettings('/tmp/test.ini')
        settings.save('foo', 'something')
        settings.save('foo.bar', 'baz')
        settings.save('foo.blah', 'boom')
        settings.save('spam', 1)
        settings.save('somepassword', '1234thisisreallysecure')

        caplog.clear()
        settings.disable_all('foo.')
        settings.write()

        assert Path('/tmp/test.ini').read_text() == snapshot
        assert caplog.record_tuples == snapshot(name='logging')

    def test_remove(self, snapshot: SnapshotAssertion) -> None:
        settings = UnixSettings('/tmp/test.ini')
        settings.save('foo', '1')
        settings.save('foo.', 2)
        settings.save('foo.bar', '3')

        settings.remove('foo.')
        settings.write()

        assert Path('/tmp/test.ini').read_text() == snapshot

    def test_get_all(self, snapshot: SnapshotAssertion) -> None:
        settings = UnixSettings('/tmp/test.ini')
        settings.save('dreamcast.foo', '1')
        settings.save('dreamcast.bar', '2')
        settings.save('dreamcast.baz', '')
        settings.save('dreamcast.ham', 'default')
        settings.save('dreamcast.spam', 'auto')
        settings.save('dreamcast.folder["/userdata/roms/dreamcast/romdir"].foo', '3')
        settings.save('dreamcast.folder["/userdata/roms/dreamcast/romdir"].bar', '4')
        settings.save('dreamcast["rom name.chd"].foo', '5')
        settings.save('dreamcast["rom name.chd"].bar', '6')
        settings.save('controllers.one', '1')
        settings.save('controllers.two', '2')
        settings.save('controllers.three', '3')

        assert settings.get_all('dreamcast') == snapshot
        assert settings.get_all('dreamcast.folder["/userdata/roms/dreamcast/romdir"]') == snapshot(name='folder')
        assert settings.get_all('dreamcast["rom name.chd"]') == snapshot(name='rom')
        assert settings.get_all('controllers', keep_name=True) == snapshot(name='with names')
        assert settings.get_all('dreamcast', keep_defaults=True) == snapshot(name='with defaults')
        assert settings.get_all('dreamcast', keep_name=True, keep_defaults=True) == snapshot(
            name='with name and defaults'
        )
