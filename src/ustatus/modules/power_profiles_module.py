import logging
from gi.repository import Gtk
from ustatus.module import Module
from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from dbus_next.errors import DBusError
from ustatus.utils.notifications import notify_error

import asyncio


class PowerProfilesModule(Module):
    def __init__(
        self,
        **kwargs,
    ) -> None:

        self.active_profile = "unknown"

        self.modal_widget = PowerProfilesModalWidget(
            set_profile_callback=lambda profile: asyncio.create_task(
                self._set_active_profile(profile)
            )
        )
        modal_menubutton = self.get_popover_menubutton(self.modal_widget)
        self.module_widget = PowerProfilesWidget(modal_menubutton, self.active_profile)

        super().__init__(module_widget=self.module_widget, **kwargs)

        self.init_dbus_task = asyncio.create_task(self._init_dbus())

    def _update(self) -> bool:
        return True

    def _update_modal(self) -> bool:
        return True

    async def _sync_profiles(self):
        self.profiles = await self.dbus_interface.get_profiles()
        self.active_profile = await self.dbus_interface.get_active_profile()

        logging.info(f"Active profile: {self.active_profile}")

        self.module_widget.set_active_profile(self.active_profile)
        self.modal_widget.set_profiles(self.profiles, self.active_profile)

    async def _set_active_profile(self, profile):
        try:
            await self.dbus_interface.set_active_profile(profile)
        except DBusError as e:
            notify_error(body=f"Error trying to change active profile: {e}")

    async def _init_dbus(self):
        bus_name = "net.hadess.PowerProfiles"
        obj_path = "/net/hadess/PowerProfiles"
        interface_name = "net.hadess.PowerProfiles"

        self.bus = await MessageBus(bus_type=BusType.SYSTEM).connect()
        introspection = await self.bus.introspect(bus_name, obj_path)
        proxy_object = self.bus.get_proxy_object(bus_name, obj_path, introspection)
        self.dbus_interface = proxy_object.get_interface(interface_name)

        self.properties_interface = proxy_object.get_interface(
            "org.freedesktop.DBus.Properties"
        )
        self.properties_interface.on_properties_changed(
            lambda _a, _b, _c: asyncio.create_task(self._sync_profiles())
        )

        await self._sync_profiles()


class PowerProfilesWidget(Gtk.Grid):
    def __init__(self, modal_menubutton, active_profile: str):
        super().__init__()

        self.set_hexpand(True)
        self.set_vexpand(True)

        self.active_profile_label = Gtk.Label()
        self.active_profile_label.set_hexpand(True)
        self.set_active_profile(active_profile)

        self.menubutton = modal_menubutton
        menubutton_image = Gtk.Image.new_from_icon_name(
            "go-down-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.menubutton.set_image(menubutton_image)
        Module.__remove_button_frame__(self.menubutton)
        self.menubutton.set_relief(Gtk.ReliefStyle.NONE)

        self.attach(self.active_profile_label, 0, 0, 1, 1)
        self.attach(self.menubutton, 0, 1, 1, 1)

    def set_active_profile(self, active_profile: str):
        self.active_profile = active_profile
        self.active_profile_label.set_label(active_profile)


class PowerProfilesModalWidget(Gtk.Box):
    def __init__(self, set_profile_callback):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.set_profile_callback = set_profile_callback
        self.show_all()

    def _set_active_profile(self, button, profile):
        if button.get_active():
            logging.info(f"Setting active profile {profile}")
            self.set_profile_callback(profile)

    def set_profiles(self, profiles, active_profile):
        self.foreach(lambda child: self.remove(child))
        profile_button = None
        for profile in profiles:
            logging.info(f"Creating button for profile {profile['Profile'].value}")
            profile_button = self._create_radiobutton(
                profile_button, profile, active_profile
            )
            self.add(profile_button)
        self.show_all()

    def _create_radiobutton(self, prev_button, profile, active_profile):
        button = Gtk.RadioButton.new_with_label_from_widget(
            prev_button, profile["Profile"].value
        )
        if profile["Profile"].value == active_profile:
            button.set_active(True)
        else:
            button.set_active(False)
        button.connect("toggled", self._set_active_profile, profile["Profile"].value)
        return button
