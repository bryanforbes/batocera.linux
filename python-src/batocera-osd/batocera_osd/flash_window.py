from __future__ import annotations

from typing import Final, cast

import gi
from gi.repository import GLib

try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')

    from gi.repository import Gdk, Gtk
except ImportError, ValueError:
    raise

_WINDOW_TITLE_FLASH: Final = 'Batocera flash'


class OSDFlashWindow(Gtk.Window):
    __gtype_name__ = 'OSDFlashWindow'

    def __init__(self) -> None:
        super().__init__(
            type=Gtk.WindowType.TOPLEVEL,
            title=_WINDOW_TITLE_FLASH,
            decorated=False,
            app_paintable=True,
            name='osd-flash-window',
        )
        self.fullscreen()

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            hexpand=True,
            vexpand=True,
            name='osd-flash-box',
        )
        self.add(box)

        self.connect('key-press-event', self.__on_event)
        self.connect('button-press-event', self.__on_event)

    def __on_event(self, _window: Gtk.Window, *_args: object) -> None:
        try:
            self.destroy()
        except Exception:
            pass

    def do_map_event(self, event: Gdk.EventAny) -> bool:
        GLib.idle_add(self.destroy)

        return super().do_map_event(event)


_css: Gtk.CssProvider | None = None


def flash(color: str, /) -> None:
    global _css

    if _css is None:
        _css = Gtk.CssProvider()
        Gtk.StyleContext.add_provider_for_screen(
            cast('Gdk.Screen', Gdk.Screen.get_default()),
            _css,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

    _css.load_from_data(
        f"""\
osd-flash-window,
osd-flash-box {{
    background-color: {color};
}}""".encode()
    )

    win = OSDFlashWindow()
    win.show_all()
