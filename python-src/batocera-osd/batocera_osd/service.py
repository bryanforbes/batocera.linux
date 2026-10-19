# ruff: ignore[missing-required-import]

from dbus_fast.annotations import DBusDouble, DBusStr, DBusUInt32  # ruff: ignore[typing-only-third-party-import]

from batocera_common.dbus import Service, dbus_method


class OSDService(Service):
    __dbus_interface_name__ = 'org.batocera.OSD'

    @dbus_method(name='FlashColor')
    def flash_color(self, color: DBusStr) -> None:
        if not color:
            color = '#ffffff'

        from .flash_window import flash

        flash(color)

    @dbus_method(name='DisplayMessage')
    def display_message(self, message: DBusStr, color: DBusStr, font_size: DBusUInt32, duration: DBusDouble) -> None:
        if not color:
            color = '#ffffff'

        if font_size <= 0:
            font_size = 36

        if duration <= 0.0:
            duration = 0.1

        from .text_window import display_text

        display_text(duration, message, color, font_size)
