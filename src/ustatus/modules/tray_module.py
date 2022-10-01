import logging
from typing import Callable, Set
from dbus_next.constants import PropertyAccess
from dbus_next.message import Message
from gi.repository import Gtk, GLib, DbusmenuGtk3, Gdk
from ustatus.config import ModuleConfig
from ustatus.module import Module
from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.signature import Variant
from dbus_next.aio.message_bus import MessageBus
from multiprocessing import Process

import asyncio


class TrayModule(Module):
    def __init__(
        self, gtk_orientation: Gtk.Orientation, update_period_seconds=3, **kwargs
    ) -> None:
        self.module_widget = TrayWidget(orientation=gtk_orientation)
        super().__init__(
            module_widget=self.module_widget, gtk_orientation=gtk_orientation, **kwargs
        )

        self.init_task = asyncio.create_task(self._init_async())

        self.show_all()
        self.module_widget.show_all()

    def _update(self) -> bool:
        self.module_widget.update()
        return True

    async def _init_async(self):
        await self._init_watcher()
        await self._init_host()
        await self._attach_to_watcher()

    async def _attach_to_watcher(self):
        bus = await MessageBus().connect()
        introspection = await bus.introspect(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher"
        )
        proxy_object = bus.get_proxy_object(
            "org.kde.StatusNotifierWatcher", "/StatusNotifierWatcher", introspection
        )
        interface = proxy_object.get_interface("org.kde.StatusNotifierWatcher")
        for merged_string in await interface.get_registered_status_notifier_items():
            logging.info(f"{merged_string}")
            await self._new_item(merged_string)

        interface.on_status_notifier_item_registered(
            lambda merged_string: self._new_item_callback(merged_string)
        )

        interface.on_status_notifier_item_unregistered(
            lambda merged_string: self.__item_removed__(merged_string)
        )

        await bus.wait_for_disconnect()

    def _new_item_callback(self, merged_string: str):
        asyncio.create_task(self._new_item(merged_string))

    async def _new_item(self, merged_string: str):
        bus_name, obj_path = service_path_from_merged(merged_string)
        item = await TrayItem.init(bus_name, obj_path)
        self.module_widget.new_item(item)

    def __item_removed__(self, merged_string: str):
        bus_name, obj_path = service_path_from_merged(merged_string)
        self.module_widget.remove_item(bus_name)

    async def _init_watcher(self):
        bus = await MessageBus().connect()
        interface = StatusNotifierWatcher("org.kde.StatusNotifierWatcher", bus)
        bus.export("/StatusNotifierWatcher", interface)
        asyncio.create_task(bus.request_name("org.kde.StatusNotifierWatcher"))
        logging.info("Watcher service initialized")

    async def _init_host(self):
        bus = await MessageBus().connect()
        interface = StatusNotifierHost("org.kde.StatusNotifierHost")
        bus.export("/StatusNotifierHost", interface)
        asyncio.create_task(bus.request_name("org.kde.StatusNotifierHost-ustatus"))
        logging.info("Host service initialized")


class TrayWidget(Gtk.FlowBox):
    def __init__(self, orientation=Gtk.Orientation.HORIZONTAL):
        super().__init__()
        match orientation:
            case Gtk.Orientation.HORIZONTAL:
                self.set_orientation(Gtk.Orientation.VERTICAL)
            case Gtk.Orientation.VERTICAL:
                self.set_orientation(Gtk.Orientation.HORIZONTAL)
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
    def __init__(self, name, bus: MessageBus):
        super().__init__(name)
        self.name = name
        self._items_registered: Set = set()
        self._hosts_registered: Set = set()
        bus.add_message_handler(self.register_sni_handler)

    def register_sni_handler(self, msg: Message):
        if msg.interface == self.name and msg.member == "RegisterStatusNotifierItem":
            self._items_registered.add(f"{msg.sender}{msg.body[0]}")
            return Message.new_method_return(msg, "", [])

    @method()
    def RegisterStatusNotifierItem(self, service: "s"):
        pass

    @method()
    def RegisterStatusNotifierHost(self, service: "s"):
        self._hosts_registered.add(service)

    @dbus_property(access=PropertyAccess.READ)
    def RegisteredStatusNotifierItems(self) -> "as":
        return list(self._items_registered)

    @dbus_property(access=PropertyAccess.READ)
    def IsStatusNotifierHostRegistered(self) -> "b":
        return len(self._hosts_registered) > 0

    @dbus_property(access=PropertyAccess.READ)
    def ProtocolVersion(self) -> "i":
        return 0


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
