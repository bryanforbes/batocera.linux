from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from typing import TYPE_CHECKING, cast

from configgen.input import Input

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion


class TestInput:
    def test_init(self, snapshot: SnapshotAssertion) -> None:
        assert Input(name='name', type='type', id='id', value='value', code=None) == snapshot

    def test_init_with_code(self, snapshot: SnapshotAssertion) -> None:
        assert Input(name='name', type='type', id='id', value='value', code='code') == snapshot

    def test_replace(self, snapshot: SnapshotAssertion) -> None:
        input = Input(name='name', type='type', id='id', value='value', code=None)

        new_input = input.replace(name='new_name')
        assert new_input == snapshot(name='name')
        assert new_input is not input

        new_input = input.replace(type='new_type')
        assert new_input == snapshot(name='type')
        assert new_input is not input

        new_input = input.replace(id='new_id')
        assert new_input == snapshot(name='id')
        assert new_input is not input

        new_input = input.replace(value='new_value')
        assert new_input == snapshot(name='value')
        assert new_input is not input

        new_input = input.replace(code='new_code')
        assert new_input == snapshot(name='code')
        assert new_input is not input

    def test_from_parent_element(self, snapshot: SnapshotAssertion) -> None:
        root = ET.fromstring("""<?xml version="1.0"?>
<inputList>
	<inputConfig type="joystick" deviceName="xin-mo.com Xinmotek Controller" deviceGUID="03000000c0160000e105000010010000">
		<input name="a" type="button" id="2" value="1" code="290"/>
		<input name="down" type="hat" id="0" value="4"/>
	</inputConfig>
</inputList>""")

        iterator = Input.from_parent_element(cast('ET.Element', root.find('./inputConfig')))
        assert isinstance(iterator, Iterator)
        assert list(iterator) == snapshot
