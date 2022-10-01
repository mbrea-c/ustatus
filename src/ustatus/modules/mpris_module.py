import logging
from typing import Any, Callable, Dict, Iterable, Optional, Set
from dbus_next.aio.message_bus import MessageBus
from dbus_next.constants import BusType
from gi.repository import Gtk
from ustatus.module import Module

import asyncio


class MprisModule(Module):
    def __init__(
        self,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)

        self._expand_widthwise()

        self.modal_widget = MprisModalWidget(self._on_select_player_callback)
        modal_menubutton = self.get_popover_menubutton(self.modal_widget)
        self.module_widget = MprisWidget(
            modal_menubutton, expander=lambda widget: self._expand_widthwise(widget)
        )
        self._expand_widthwise(self.module_widget)

        self.bus_names: Set[str] = set()
        self.init_dbus_task = asyncio.create_task(self.__init_dbus__())

        self.set_module_widget(self.module_widget)

    def _update(self) -> bool:
        return True

    def _update_modal(self) -> bool:
        return True

    def _on_name_owner_changed_callback(
        self, name: str, old_owner: str, new_owner: str
    ):
        if name.startswith("org.mpris.MediaPlayer2"):
            if new_owner:
                self.bus_names.add(name)
            else:
                self.bus_names.remove(name)
                if self.selected_player == name:
                    self._on_select_player_callback(None)
            self.modal_widget.set_items(self.bus_names)

    def _on_play_pause_callback(self):
        if self.mpris_interface:
            asyncio.create_task(self._on_play_pause())

    async def _on_play_pause(self):
        await self.mpris_interface.call_play_pause()

    def _on_next_callback(self):
        if self.mpris_interface:
            asyncio.create_task(self._on_next())

    async def _on_next(self):
        await self.mpris_interface.call_next()

    def _on_prev_callback(self):
        if self.mpris_interface:
            asyncio.create_task(self._on_prev())

    async def _on_prev(self):
        await self.mpris_interface.call_previous()

    def _on_properties_changed_callback(self, bus_name, props, other):
        asyncio.create_task(self.__on_properties_changed__(props))

    def handle_change_playback_status(self, value: str):
        self.module_widget.set_playback_status(value)

    def handle_change_can_go_next(self, value: bool):
        if value:
            self.module_widget.set_on_next(self._on_next_callback)
        else:
            self.module_widget.set_on_next(None)

    def handle_change_can_go_previous(self, value: bool):
        if value:
            self.module_widget.set_on_previous(self._on_prev_callback)
        else:
            self.module_widget.set_on_previous(None)

    async def __on_properties_changed__(self, props: Dict[str, Any]):
        for key in props.keys():
            if key == "PlaybackStatus":
                playback_status = props[key].value
                assert isinstance(playback_status, str)
                self.handle_change_playback_status(playback_status)
            elif key == "CanGoNext":
                can_go_next = props[key].value
                assert isinstance(can_go_next, bool)
                self.handle_change_can_go_next(can_go_next)
            elif key == "CanGoPrevious":
                can_go_prev = props[key].value
                assert isinstance(can_go_prev, bool)
                self.handle_change_can_go_previous(can_go_prev)
            elif key == "Metadata":
                title = props[key].value.get("xesam:title")
                if title:
                    title = title.value
                self.modal_widget.set_title(title)

    def _on_select_player_callback(self, name):
        asyncio.create_task(self._select_player(name))

    async def _select_player(self, bus_name: Optional[str]):
        logging.info(f"binding with {bus_name}")
        obj_path = "/org/mpris/MediaPlayer2"
        mpris_interface_name = "org.mpris.MediaPlayer2.Player"
        props_interface_name = "org.freedesktop.DBus.Properties"

        if bus_name:
            introspection = await self.bus.introspect(bus_name, obj_path)
            proxy_object = self.bus.get_proxy_object(bus_name, obj_path, introspection)
            self.mpris_interface = proxy_object.get_interface(mpris_interface_name)
            self.mpris_props_interface = proxy_object.get_interface(
                props_interface_name
            )

            self.selected_player = bus_name
            self.mpris_props_interface.on_properties_changed(
                self._on_properties_changed_callback
            )
            self.module_widget.set_on_play_pause(self._on_play_pause_callback)
            self.modal_widget.set_title(await self._get_title())

            playback_status = await self.mpris_interface.get_playback_status()
            self.handle_change_playback_status(playback_status)

            can_go_next = await self.mpris_interface.get_can_go_next()
            self.handle_change_can_go_next(can_go_next)

            can_go_prev = await self.mpris_interface.get_can_go_previous()
            self.handle_change_can_go_previous(can_go_prev)
        else:
            self.mpris_interface = None
            self.mpris_props_interface = None
            self.selected_player = None
            self.module_widget.set_on_play_pause(None)
            self.handle_change_playback_status("Paused")
            self.handle_change_can_go_next(False)
            self.handle_change_can_go_prev(False)

    async def _get_title(self):
        metadata: Dict = await self.mpris_interface.get_metadata()
        title = metadata.get("xesam:title")
        if title:
            title = title.value
        return title

    async def __init_dbus__(self):
        bus_name = "org.freedesktop.DBus"
        obj_path = "/org/freedesktop/DBus"

        self.bus = await MessageBus(bus_type=BusType.SESSION).connect()
        introspection = await self.bus.introspect(bus_name, obj_path)
        proxy_object = self.bus.get_proxy_object(bus_name, obj_path, introspection)
        self.dbus_interface = proxy_object.get_interface("org.freedesktop.DBus")

        self.dbus_interface.on_name_owner_changed(self._on_name_owner_changed_callback)

        names = await self.dbus_interface.call_boxlist_names()
        for name in names:
            if name.startswith("org.mpris.MediaPlayer2"):
                self.bus_names.add(name)
        self.modal_widget.set_items(self.bus_names)


class MprisWidget(Gtk.Grid):
    def __init__(self, modal_menubutton, expander):
        super().__init__()
        # self.set_column_homogeneous(False)
        # self.set_row_homogeneous(False)

        self.button_play = Gtk.Button.new()
        self.button_play_image = Gtk.Image.new()
        self.button_play.set_image(self.button_play_image)
        self.button_play.set_relief(Gtk.ReliefStyle.NONE)
        self.button_play.set_sensitive(False)
        self.set_playback_status("Paused")
        Module.__remove_button_frame__(self.button_play)

        self.button_prev = Gtk.Button.new_from_icon_name(
            "media-skip-backward-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.button_prev.set_relief(Gtk.ReliefStyle.NONE)
        self.button_prev.set_sensitive(False)
        Module.__remove_button_frame__(self.button_prev)

        self.button_next = Gtk.Button.new_from_icon_name(
            "media-skip-forward-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.button_next.set_relief(Gtk.ReliefStyle.NONE)
        self.button_next.set_sensitive(False)
        Module.__remove_button_frame__(self.button_next)

        self.menubutton = modal_menubutton
        menubutton_image = Gtk.Image.new_from_icon_name(
            "go-down-symbolic", Gtk.IconSize.SMALL_TOOLBAR
        )
        self.menubutton.set_image(menubutton_image)
        Module.__remove_button_frame__(self.menubutton)
        self.menubutton.set_relief(Gtk.ReliefStyle.NONE)
        expander(self.menubutton)

        self.attach(self.button_prev, 0, 0, 1, 1)
        self.attach(self.button_play, 1, 0, 1, 1)
        self.attach(self.button_next, 2, 0, 1, 1)
        self.attach(self.menubutton, 0, 1, 3, 1)

    def set_playback_status(self, playback_status):
        if playback_status == "Playing":
            self.button_play_image.set_from_icon_name(
                "media-playback-pause-symbolic", Gtk.IconSize.SMALL_TOOLBAR
            )
        elif playback_status == "Paused":
            self.button_play_image.set_from_icon_name(
                "media-playback-start-symbolic", Gtk.IconSize.SMALL_TOOLBAR
            )

    def set_on_play_pause(self, on_play_pause: Optional[Callable]):
        if on_play_pause:
            self.on_play_pause = on_play_pause
            self.button_play_handler_id = self.button_play.connect(
                "clicked", lambda button: on_play_pause()
            )
            self.button_play.set_sensitive(True)
        else:
            self.on_play_pause = None
            self.button_play.disconnect(self.button_play_handler_id)
            self.button_play.set_sensitive(False)

    def set_on_next(self, on_next: Optional[Callable]):
        if on_next:
            self.on_next = on_next
            self.button_next_handler_id = self.button_next.connect(
                "clicked", lambda button: on_next()
            )
            self.button_next.set_sensitive(True)
        else:
            self.on_next = None
            if hasattr(self, "button_next_handler_id"):
                self.button_next.disconnect(self.button_next_handler_id)
            self.button_next.set_sensitive(False)

    def set_on_previous(self, on_prev: Optional[Callable]):
        if on_prev:
            self.on_prev = on_prev
            self.button_prev_handler_id = self.button_prev.connect(
                "clicked", lambda button: on_prev()
            )
            self.button_prev.set_sensitive(True)
        else:
            self.on_prev = None
            if hasattr(self, "button_prev_handler_id"):
                self.button_prev.disconnect(self.button_prev_handler_id)

            self.button_prev.set_sensitive(False)


class MprisModalWidget(Gtk.Box):
    def __init__(self, on_select):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.combo = Gtk.ComboBoxText()
        self.add(self.combo)
        self.on_select = on_select
        self.combo.connect("changed", self.on_select_changed)
        self.label_title = Gtk.Label()
        self.add(self.label_title)

    def on_select_changed(self, combo):
        active = self.combo.get_active_text()
        if active is not None:
            self.on_select(active)

    def set_title(self, title: Optional[str]):
        if title:
            self.label_title.set_label(f"Title: {title}")
        else:
            self.label_title.set_label("Title: Unknown")

    def set_items(self, items: Iterable):
        self.combo.remove_all()
        for item in items:
            self.combo.set_active_id(item)
            self.combo.append_text(item)
