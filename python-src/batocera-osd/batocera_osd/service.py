# ruff: ignore[missing-required-import]

from typing import TYPE_CHECKING, Final, cast

from dbus_fast.annotations import DBusDouble, DBusStr, DBusUInt32

from batocera_common.dbus import Service, dbus_method

if TYPE_CHECKING:
    from gi.repository import Gtk

WINDOW_TITLE_FLASH: Final = 'Batocera flash'
WINDOW_TITLE_OSD: Final = 'Batocera OSD'


def build_fullscreen_flash(color: str, /) -> Gtk.Window:
    import gi

    try:
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')

        from gi.repository import Gdk, Gtk
    except ImportError, ValueError:
        raise

    win = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
    win.set_title(WINDOW_TITLE_FLASH)
    win.set_decorated(False)
    win.set_app_paintable(True)
    win.fullscreen()

    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
    box.set_hexpand(True)
    box.set_vexpand(True)
    win.add(box)

    css = Gtk.CssProvider()
    css.load_from_data(f'window, box {{ background-color: {color}; }}'.encode())
    Gtk.StyleContext.add_provider_for_screen(
        cast('Gdk.Screen', Gdk.Screen.get_default()),
        css,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )

    def close(_window: Gtk.Window, *_args: object) -> None:
        try:
            win.destroy()
        except Exception:
            pass

    win.connect('key-press-event', close)
    win.connect('button-press-event', close)

    return win


class OSDService(Service):
    __dbus_interface_name__ = 'org.batocera.OSD'

    @dbus_method(name='FlashColor')
    def flash_color(self, color: DBusStr, duration: DBusDouble) -> None:
        if not color:
            color = '#ffffff'

        if duration <= 0.0:
            duration = 0.1

    @dbus_method(name='DisplayMessage')
    def display_message(self, message: DBusStr, color: DBusStr, font_size: DBusUInt32, duration: DBusDouble) -> None:
        if not color:
            color = '#ffffff'

        if font_size <= 0:
            font_size = 36

        if duration <= 0.0:
            druation = 0.1
