from typing import Callable
from gi.repository import Gtk, GLib
import pulsectl_asyncio, asyncio
from pystatus.graphics.volume import Volume
from pystatus.module import Module


class VolumeModule(Gtk.Frame):
    def __init__(
        self, gtk_orientation: Gtk.Orientation, toggle_modal: Callable
    ) -> None:
        super().__init__()

        container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.sink_container = Gtk.Box(orientation=gtk_orientation, spacing=5)
        label = Gtk.Label(label="Volume")

        container.add(label)
        container.add(self.sink_container)

        self.add(container)

        self.sinks = dict()
        self.pulse = pulsectl_asyncio.PulseAsync("pystatus")

        self.updater_task = asyncio.create_task(self._init_async())
        self.update_lock = False

    def _update_sinks(self, name_volume_dict: dict):
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
        pending_removal = []
        for name, label in self.sinks.items():
            if name not in name_volume_dict.keys():
                pending_removal.append((name, label))
        for name, label in pending_removal:
            self.sink_container.remove(label)
            self.sinks.pop(name)

    async def _init_async(self):
        await self.pulse.connect()
        await self._update()
        async for _ in self.pulse.subscribe_events("all"):
            await self._update()

    async def _update(self) -> None:
        if not self.update_lock:
            self.update_lock = True
            sinks = await self.pulse.sink_list()
            name_volume_dict = {
                s.name: await self.pulse.volume_get_all_chans(s) for s in sinks
            }
            self._update_sinks(name_volume_dict)
            self.queue_draw()
            self.update_lock = False


class SinkVolume(Gtk.Box):
    def __init__(self, name: str, volume: float) -> None:
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        self.label = Gtk.Label(label=self._label(volume))
        self.meter = Volume(volume)
        self.meter.set_size_request(25, 25)
        self.set_tooltip_text(name)
        self.add(self.meter)
        self.add(self.label)
        self.show_all()

    def update(self, volume: float) -> None:
        self.label.set_label(self._label(volume))
        self.meter.update(volume)

    def _label(self, volume: float) -> str:
        return f"{volume * 100:.0f}%"
