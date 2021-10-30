from gi.repository import Gtk, GLib
import pulsectl_asyncio, asyncio


class VolumeModule(Gtk.Frame):
    def __init__(self, min_update_interval_seconds=0.2) -> None:
        super().__init__()

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sink_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        label = Gtk.Label(label="Volume")

        container.add(label)
        container.add(self.sink_container)

        self.add(container)

        self.sinks = dict()
        self.pulse = pulsectl_asyncio.PulseAsync("pystatus")

        self.updater_task = asyncio.create_task(self.__init_async__())
        # self.update()
        # GLib.timeout_add(update_period_seconds * 1000, lambda: self.update())

    def __update_sinks__(self, name_volume_dict: dict):
        # New additions and updates
        for name, volume in name_volume_dict.items():
            if name in self.sinks.keys():
                label = self.sinks[name]
                label.set_label(f"{volume * 100:.0f}%")
            else:
                label = Gtk.Label(label=f"{volume * 100:.0f}%")
                self.sink_container.add(label)
                self.sinks[name] = label
                label.show()
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
