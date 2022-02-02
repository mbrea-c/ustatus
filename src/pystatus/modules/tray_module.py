from gi.repository import Gtk, GLib, DbusmenuGtk3, Gdk
from pystatus.module import Module
from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.signature import Variant
from dbus_next.aio.message_bus import MessageBus

import asyncio


class TrayModule(Module):
    def __init__(self, update_period_seconds=3) -> None:
        self.module_widget = TrayWidget()
        super().__init__(self.module_widget)

        self.__update__()
        GLib.timeout_add(update_period_seconds * 1000, lambda: self.__update__())

        # Not start another watcher yet, as we are still running swaybar
        # self.watcher_task = asyncio.create_task(self.__init_watcher__())
        self.host_task = asyncio.create_task(self.__init_host__())
        self.attach_to_watcher_task = asyncio.create_task(self.__attach_to_watcher__())

    def __update__(self) -> bool:
        self.module_widget.update()
        return True

    async def __attach_to_watcher__(self):
        bus = await MessageBus().connect()
        introspection = await bus.introspect(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher"
        )
        proxy_object = bus.get_proxy_object(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher", introspection
        )
        interface = proxy_object.get_interface("org.kde.StatusNotifierWatcher")
        for merged_string in await interface.get_registered_status_notifier_items():
            await self.__new_item__(merged_string)

        interface.on_status_notifier_item_registered(
            lambda merged_string: self.__new_item_callback__(merged_string)
        )

        interface.on_status_notifier_item_unregistered(
            lambda merged_string: self.__item_removed__(merged_string)
        )

        await bus.wait_for_disconnect()

    def __new_item_callback__(self, merged_string: str):
        asyncio.create_task(self.__new_item__(merged_string))

    async def __new_item__(self, merged_string: str):
        bus_name, obj_path = service_path_from_merged(merged_string)
        item = await TrayItem.init(bus_name, obj_path)
        self.module_widget.new_item(item)

    def __item_removed__(self, merged_string: str):
        bus_name, obj_path = service_path_from_merged(merged_string)
        self.module_widget.remove_item(bus_name)

    async def __init_watcher__(self):
        bus = await MessageBus().connect()
        interface = StatusNotifierWatcher("org.kde.StatusNotifierWatcher")
        bus.export("/StatusNotifierWatcher", interface)
        await bus.request_name("org.kde.StatusNotifierWatcher")
        await asyncio.get_event_loop().create_future()

    async def __init_host__(self):
        bus = await MessageBus().connect()
        interface = StatusNotifierHost("org.kde.StatusNotifierHost")
        bus.export("/StatusNotifierHost", interface)
        await bus.request_name("org.kde.StatusNotifierHost-pystatus")
        await asyncio.get_event_loop().create_future()


class TrayWidget(Gtk.FlowBox):
    def __init__(self):
        super().__init__()
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.items = dict()

    def update(self):
        self.show_all()

    def new_item(self, item):
        self.items[item.bus_name] = item
        self.add(item)
        self.update()

    def remove_item(self, bus_name):
        if bus_name in self.items:
            item = self.items[bus_name]
            self.remove(item)


class TrayItem(Gtk.Box):
    interface_name = "org.kde.StatusNotifierItem"

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL)

    @classmethod
    async def init(cls, bus_name, obj_path):
        obj = cls()

        obj.button_icon = Gtk.Image()

        obj.button = Gtk.Button()
        obj.button.set_relief(Gtk.ReliefStyle.NONE)
        obj.button.set_image(obj.button_icon)
        obj.button.set_focus_on_click(False)

        Module.__remove_button_frame__(obj.button)
        obj.add(obj.button)
        obj.bus_name = bus_name
        obj.obj_path = obj_path
        obj.bus = await MessageBus().connect()
        introspection = await obj.bus.introspect(bus_name, obj_path)
        proxy_object = obj.bus.get_proxy_object(bus_name, obj_path, introspection)
        obj.interface = proxy_object.get_interface(cls.interface_name)
        await obj.__get_id__()
        await obj.__get_title__()
        await obj.__get_icon_name__()
        await obj.__get_menu__()

        obj.interface.on_new_title(lambda: obj.__on_new_title_callback__())
        obj.interface.on_new_icon(lambda: obj.__on_new_icon_callback__())

        return obj

    def __on_new_title_callback__(self):
        asyncio.create_task(self.__get_title__())

    def __on_new_icon_callback__(self):
        asyncio.create_task(self.__get_icon_name__())

    async def __get_id__(self):
        self.id = await self.interface.get_id()

    async def __get_title__(self):
        self.title = await self.interface.get_title()

    async def __get_icon_name__(self):
        self.icon_name = await self.interface.get_icon_name()
        self.button_icon.set_from_icon_name(self.icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        self.show_all()

    async def __get_menu_path__(self):
        self.menu_path = await self.interface.get_menu()

    async def __get_menu__(self):
        await self.__get_menu_path__()
        self.menu = DbusmenuGtk3.Menu.new(self.bus_name, self.menu_path)
        self.menu.attach_to_widget(self.button)
        self.menu.set_take_focus(True)
        self.button.connect("clicked", self.__on_button_clicked__)
        self.show_all()

    def __on_button_clicked__(self, widget):
        self.menu.popup_at_widget(
            widget, Gdk.Gravity.CENTER, Gdk.Gravity.NORTH_WEST, None
        )


class StatusNotifierWatcher(ServiceInterface):
    def __init__(self, name):
        super().__init__(name)
        self._string_prop = "kevin"

    @method()
    def Echo(self, what: "s") -> "s":
        return what

    @method()
    def GetVariantDict() -> "a{sv}":
        return {
            "foo": Variant("s", "bar"),
            "bat": Variant("x", -55),
            "a_list": Variant("as", ["hello", "world"]),
        }

    @dbus_property()
    def string_prop(self) -> "s":
        return self._string_prop

    @string_prop.setter
    def string_prop_setter(self, val: "s"):
        self._string_prop = val

    @signal()
    def signal_simple(self) -> "s":
        return "hello"


class StatusNotifierHost(ServiceInterface):
    def __init__(self, name):
        super().__init__(name)


def service_path_from_merged(merged: str):
    split_list = merged.split("/", maxsplit=1)
    if len(split_list) == 1:
        return merged, "/StatusNotifierItem"
    elif len(split_list) == 2:
        service, path = split_list
        path = "/" + path
        return service, path
    else:
        raise Exception("Error while splitting merged service/path string")
