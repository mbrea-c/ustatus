import pystatus
from pystatus.module import Module
from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.signature import Variant
from dbus_next.aio.message_bus import MessageBus
import asyncio


async def init_service(on_hide, on_show):
    bus = await MessageBus().connect()
    interface = PystatusRemoteService(
        "pystatus.PystatusRemoteService", on_show, on_hide
    )
    bus.export("/PystatusRemoteService", interface)
    # now that we are ready to handle requests, we can request name from D-Bus
    await bus.request_name("pystatus.PystatusRemoteService")
    # wait indefinitely
    await asyncio.get_event_loop().create_future()


class PystatusRemoteService(ServiceInterface):
    def __init__(self, name, on_show, on_hide):
        super().__init__(name)
        self._string_prop = "kevin"
        self.on_show = on_show
        self.on_hide = on_hide
        self.is_shown = True

    @method()
    def Hide(self):
        print("Hide called")
        self.on_hide()
        self.is_shown = False

    @method()
    def Show(self):
        print("Show called")
        self.on_show()
        self.is_shown = True

    @method()
    def ToggleVisible(self):
        print("Toggle called")
        if self.is_shown:
            self.on_hide()
        else:
            self.on_show()
        self.is_shown = not self.is_shown
