from gi.repository import Gtk, GLib
import pulsectl_asyncio, asyncio
from pystatus.graphics.volume import Volume
from pystatus.module import Module


class VolumeModule(Gtk.Frame):
    def __init__(self) -> None:
        super().__init__()

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sink_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        label = Gtk.Label(label="Volume")

        container.add(label)
        container.add(self.sink_container)

        self.add(container)

        self.sinks = dict()
        self.pulse = pulsectl_asyncio.PulseAsync("pystatus")

        self.updater_task = asyncio.create_task(self.__init_async__())

    def __update_sinks__(self, name_volume_dict: dict):
        # New additions and updates
        for name, volume in name_volume_dict.items():
            if name in self.sinks.keys():
                label = self.sinks[name]
                label.update(volume)
            else:
                label = SinkVolume(name, volume)
                self.sink_container.add(label)
                self.sinks[name] = label
        # Removals
        for name, label in self.sinks.items():
            if name not in name_volume_dict.keys():
                self.sink_container.remove(label)
                self.sinks.pop(name)

    async def __init_async__(self):
        await self.pulse.connect()
        await self.__update__()
        async for _ in self.pulse.subscribe_events("all"):
            await self.__update__()

    async def __update__(self) -> None:
        sinks = await self.pulse.sink_list()
        name_volume_dict = {
            s.name: await self.pulse.volume_get_all_chans(s) for s in sinks
        }
        self.__update_sinks__(name_volume_dict)
        self.queue_draw()


class SinkVolume(Gtk.Box):
    def __init__(self, name: str, volume: float) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.label = Gtk.Label(label=self.__label__(volume))
        self.meter = Volume(volume)
        self.meter.set_size_request(25, 25)
        self.set_tooltip_text(name)
        self.add(self.meter)
        self.add(self.label)
        self.show_all()

    def update(self, volume: float) -> None:
        self.label.set_label(self.__label__(volume))
        self.meter.update(volume)

    def __label__(self, volume: float) -> str:
        return f"{volume * 100:.0f}%"
