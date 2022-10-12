from typing import Callable
from dbus_next.aio.message_bus import MessageBus
from gi.repository import Gtk, GLib
from pulsectl import pulsectl
import pulsectl_asyncio, asyncio
from python_dbus_system_api.interfaces.volume import VolumeInterface

from python_reactive_ui import Component, use_state
from python_reactive_ui.backends.gtk3.builtin.box import Box
from python_reactive_ui.backends.gtk3.builtin.label import Label
from python_reactive_ui.backends.gtk3.builtin.progress_bar import ProgressBar
from python_reactive_ui.lib.hooks import use_effect
from ustatus.config import ModuleConfig
from ustatus.graphics.meter import Meter
from ustatus.graphics.volume import Volume
from ustatus.module import Module


class Volume(Component):
    async def _setup_client(self, set_client, set_sinks):
        name = "pysysapi.api"
        path = "/pysysapi"
        bus = await MessageBus().connect()
        introspection = await bus.introspect(name, path)
        proxy_object = bus.get_proxy_object(name, path, introspection)
        interface = proxy_object.get_interface(VolumeInterface.INAME)
        interface.on_event(
            lambda event: asyncio.create_task(self._update_sinks(interface, set_sinks))
        )
        await self._update_sinks(interface, set_sinks)
        set_client(interface)

    async def _update_sinks(self, client, set_sinks):
        set_sinks(await client.call_get_sinks())

    def _render(self, props, children):
        sinks, set_sinks = use_state(self, dict())
        client, set_client = use_state(self, None)
        use_effect(
            self,
            lambda: asyncio.create_task(self._setup_client(set_client, set_sinks)),
            [],
        )

        return Box(
            {"hexpand": True, "halign": "center", "size_request": (-1, 60)},
            [
                Box(
                    {
                        "orientation": "vertical",
                        "opacity": 0.5 if sink["mute"].value == 1 else 1.0,
                        "tooltip_text": sink["description"].value,
                    },
                    [
                        ProgressBar(
                            {
                                "orientation": "vertical",
                                "fraction": sink["volume_all_chans"].value,
                                "vexpand": True,
                                "inverted": True,
                                "hexpand": True,
                                "halign": "center",
                            }
                        ),
                        Label({"text": f"{100 * sink['volume_all_chans'].value:.0f}%"}),
                    ],
                )
                for sink in sinks
            ],
        )
