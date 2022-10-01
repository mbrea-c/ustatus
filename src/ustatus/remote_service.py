import ustatus
from ustatus.module import Module
from dbus_next.service import ServiceInterface, method, dbus_property, signal
from dbus_next.signature import Variant
from dbus_next.aio.message_bus import MessageBus
import asyncio
import logging


async def init_service(on_hide, on_show, bar_name):
    bus = await MessageBus().connect()
    interface = UstatusRemoteService("ustatus.UstatusRemoteService", on_show, on_hide)
    bus.export("/UstatusRemoteService", interface)
    # now that we are ready to handle requests, we can request name from D-Bus
    asyncio.create_task(bus.request_name(f"ustatus.UstatusRemoteService.{bar_name}"))
    logging.info("Remote service initialized")


class UstatusRemoteService(ServiceInterface):
    def __init__(self, name, on_show, on_hide):
        super().__init__(name)
        self.on_show = on_show
        self.on_hide = on_hide
        self.is_shown = True

    @method()
    def Hide(self):
        logging.info("Hide called")
        self.on_hide()
        self.is_shown = False

    @method()
    def Show(self):
        logging.info("Show called")
        self.on_show()
        self.is_shown = True

    @method()
    def ToggleVisible(self):
        logging.info("Toggle called")
        if self.is_shown:
            self.on_hide()
        else:
            self.on_show()
        self.is_shown = not self.is_shown
