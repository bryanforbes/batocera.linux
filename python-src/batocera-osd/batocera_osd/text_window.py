from __future__ import annotations

import os
from typing import Final

import gi
from gi.repository import GLib, GObject

try:
    gi.require_version('Gtk', '3.0')
    gi.require_version('Gdk', '3.0')

    from gi.repository import Gdk, Gtk, Pango
except ImportError, ValueError:
    raise

_WINDOW_TITLE_OSD: Final = 'Batocera OSD'


def _get_primary_geometry() -> tuple[int, int, int, int]:
    display = Gdk.Display.get_default()
    mon = None

    if display is None:
        mon = None
    else:
        mon = display.get_primary_monitor()

        if mon is None:
            mon = display.get_monitor(0)

    if mon and hasattr(mon, 'get_geometry'):
        g = mon.get_geometry()

        if g.height > g.width:
            (g.width, g.height) = (g.height, g.width)  # some handhelds

        return g.x, g.y, g.width, g.height

    return (0, 0, 1280, 720)


class OSDTextWindow(Gtk.Window):
    __gtype_name__ = 'OSDTextWindow'

    _duration: float
    _realize_dimenstions: tuple[int, int, int, int]
    _revealer: Gtk.Revealer
    _label: Gtk.Label

    def __init__(self, duration: float, text: str, text_color: str, font_size: int, /) -> None:
        super().__init__(
            type=Gtk.WindowType.TOPLEVEL,
            name='osd-text-window',
            title=_WINDOW_TITLE_OSD,
            decorated=False,
            app_paintable=True,  # allow CSS color
        )

        css = Gtk.CssProvider()
        css.load_from_data(
            f"""\
osd-text-box {{ background-color: #000000; }}
osd-text-label {{ color: {text_color}; }}
""".encode()
        )

        self.get_style_context().add_provider(css, Gtk.STYLE_PROVIDER_PRIORITY_USER)

        out_x, out_y, out_w, _ = _get_primary_geometry()
        height_px = max(12, font_size + 10)

        self._duration = duration
        self._realize_dimenstions = (out_x, out_y, out_w, height_px)

        self._revealer = Gtk.Revealer(
            name='osd-text-revealer',
            transition_type=Gtk.RevealerTransitionType.NONE,
            transition_duration=0,
            reveal_child=True,
            width_request=out_w,
            height_request=height_px,
            hexpand=True,
            vexpand=True,
        )
        self.add(self._revealer)

        box = Gtk.Box(
            name='osd-text-box',
            orientation=Gtk.Orientation.VERTICAL,
            width_request=out_w,
            height_request=height_px,
            hexpand=True,
            vexpand=True,
            margin_top=2,
            margin_bottom=2,
            margin_start=12,
            margin_end=12,
        )
        self._revealer.add(box)

        pango_attrs = Pango.AttrList()
        pango_attrs.insert(Pango.attr_size_new(int(font_size * Pango.SCALE)))

        self._label = Gtk.Label(
            label=text,
            name='osd-text-label',
            justify=Gtk.Justification.CENTER,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            wrap=True,
            wrap_mode=Pango.WrapMode.WORD_CHAR,
            max_width_chars=256,
            attributes=pango_attrs,
        )
        self._label.get_style_context().add_class('overlay-text')

        box.pack_start(self._label, True, True, 0)

        self.connect('key-press-event', self.__on_close)
        self.connect('button-press-event', self.__on_close)

    def do_realize(self) -> None:
        out_x, out_y, out_w, height_px = self._realize_dimenstions

        if os.environ.get('WAYLAND_DISPLAY'):
            # Wayland/labwc: only size, don't move
            self.resize(out_w, height_px)
        else:
            # X11: manual positioning required
            width = out_w
            x = out_x + (out_w - width) // 2
            y = out_y + 2
            self.move(max(0, x), max(0, y))
            self.resize(width, height_px)

        return super().do_realize()

    def do_map_event(self, event: Gdk.EventAny) -> bool:
        total_ms = max(300, int(self._duration * 1000))
        fade_ms = min(300, total_ms)

        GLib.timeout_add(max(1, total_ms - fade_ms), self.__fade_out, fade_ms)

        return super().do_map_event(event)

    def __on_close(self, _window: Gtk.Window, *_args: object) -> None:
        try:
            self.destroy()
        except Exception:
            pass

    def __on_fade_out_complete(self, revealer: Gtk.Revealer, _param: GObject.ParamSpec) -> None:
        if not revealer.props.child_revealed:
            self.__on_close(self)

    def __fade_out(self, fade_ms: int) -> None:
        self._revealer.set_transition_type(Gtk.RevealerTransitionType.CROSSFADE)
        self._revealer.set_transition_duration(fade_ms)
        self._revealer.connect('notify::child-revealed', self.__on_fade_out_complete)
        self._revealer.set_reveal_child(False)


OSDTextWindow.set_css_name('osd-text-window')  # pyright: ignore


def display_text(duration: float, text: str, text_color: str, font_size: int, /) -> None:
    win = OSDTextWindow(duration, text, text_color, font_size)
    win.show_all()
