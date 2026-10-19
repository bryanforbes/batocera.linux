# This file is part of The Batocera Linux Distribution (https://batocera.org).
# Copyright (c) 2026 The Batocera Team.
#
# The Batocera Linux Distribution is free software: you can redistribute it
# and/or modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# The Batocera Linux Distribution is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with The Batocera Linux Distribution. If not, see
# <https://www.gnu.org/licenses/>.
#
# YOU MUST RETAIN THE LICENSE AND COPYRIGHT NOTICES ABOVE IN ANY
# REDISTRIBUTED VERSION OF THIS FILE.

from __future__ import annotations

import importlib
from argparse import ArgumentParser, Namespace
from pathlib import Path

from batocera_common.dbus._generate_proxies import generate_proxies

_GENERATE_PROXIES_COMMAND = 'generate-proxies'


def _generate_proxies(args: Namespace, /) -> None:
    generate_proxies(args.xml_file, args.interface_prefix, args.output_file)


def _generate_xml(args: Namespace, /) -> None:
    module_name, class_name = args.class_spec.rsplit(':', 1)
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)

    if args.output_file is not None:
        args.output_file.write_text(cls.get_xml())
    else:
        print(cls.get_xml())


parser = ArgumentParser()
subparsers = parser.add_subparsers(required=True)

generate_proxies_parser = subparsers.add_parser(_GENERATE_PROXIES_COMMAND)
generate_proxies_parser.add_argument(
    'xml_file',
    type=Path,
    help='The XML file to parse.',
)
generate_proxies_parser.add_argument(
    'interface_prefix',
    type=str,
    help='The prefix to use for generated interface names (e.g. "batocera_common.connman.interfaces").',
)
generate_proxies_parser.add_argument(
    'output_file',
    type=Path,
    help='The file to write the generated client proxy code to (defaults to `proxies.py` as a sibling of the module argument).',
)
generate_proxies_parser.set_defaults(command_handler=_generate_proxies)

generate_xml_parser = subparsers.add_parser('generate-xml')
generate_xml_parser.add_argument(
    'class_spec',
    type=str,
    help='The class to generate XML for (e.g. "hotkeygen.dbus.interfaces:HotkeygenService").',
)
generate_xml_parser.add_argument(
    'output_file',
    type=Path,
    nargs='?',
    help='The file to write the generated XML to (prints to stdout if not provided).',
)
generate_xml_parser.set_defaults(command_handler=_generate_xml)

args = parser.parse_args()
args.command_handler(args)
