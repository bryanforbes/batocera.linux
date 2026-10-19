from __future__ import annotations

from typing import ClassVar

from dbus_fast.service import (
    ServiceInterface,
    dbus_method as dbus_method,
    dbus_property as dbus_property,
    dbus_signal as dbus_signal,
)


class Service(ServiceInterface):
    __dbus_interface_name__: ClassVar[str]

    def __init__(self) -> None:
        super().__init__(self.__dbus_interface_name__)

    @classmethod
    def get_xml(cls):
        import xml.etree.ElementTree as ET

        from dbus_fast.introspection import Node

        service = cls.__new__(cls)
        Service.__init__(service)

        xml = Node(interfaces=[service.introspect()]).to_xml()
        xml.attrib['name'] = '/'
        ET.indent(xml)

        return f"""\
<!DOCTYPE node PUBLIC
"-//freedesktop//DTD D-BUS Object Introspection 1.0//EN"
"http://www.freedesktop.org/standards/dbus/1.0/introspect.dtd">
{ET.tostring(xml, encoding='unicode')}
"""
